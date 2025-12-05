from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User
from django.db import OperationalError, transaction
from .models import Producto, Artista, Usuario, Pedido, DetallePedido, Cart, CartItem
from .forms import ArtistaForm, ProductoForm, UsuarioForm
from django.contrib.auth.models import User, Group
from django.contrib.auth.forms import UserCreationForm

# Vista pública de detalle de artista
def artista_detalle(request, artista_id):
    artista = get_object_or_404(Artista, id=artista_id)
    productos = Producto.objects.filter(artista=artista)
    return render(request, 'artista_detalle.html', {
        'artista': artista,
        'productos': productos,
    })


# ----------------------
# Autenticación y registro
# ----------------------
def register_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        account_type = request.POST.get('account_type')  # 'employee' o 'client'
        
        if not username or not email or not password or not account_type:
            messages.error(request, 'Todos los campos son obligatorios.')
            return redirect('register')

        if User.objects.filter(username=username).exists():
            messages.error(request, 'El nombre de usuario ya existe.')
            return redirect('register')

        # Crear usuario con is_staff basado en el tipo de cuenta
        is_staff = (account_type == 'employee')
        user = User.objects.create_user(
            username=username, 
            email=email, 
            password=password,
            is_staff=is_staff
        )
        
        # Si es empleado, agregarlo al grupo 'Empleados'
        if is_staff:
            group, _ = Group.objects.get_or_create(name='Empleados')
            user.groups.add(group)
        else:
            # Si es cliente, crear el perfil Usuario (se crea automáticamente por señal)
            pass
        
        messages.success(request, 'Cuenta creada correctamente. Por favor inicia sesión.')
        return redirect('login_frontend')

    return render(request, 'register.html')


def login_frontend(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            # Si es staff, enviarlo al panel de administración
            if user.is_staff:
                return redirect('inicio_axolotlmusic')
            return redirect('index_frontend')
        else:
            messages.error(request, 'Usuario o contraseña incorrectos.')
            return redirect('login_frontend')

    return render(request, 'login.html')


def logout_view(request):
    logout(request)
    return redirect('index_frontend')


# ----------------------
# Comprobadores
# ----------------------
def is_staff_user(user):
    return user.is_staff


def _safe_clientes_list():
    """Devuelve un queryset de `Usuario` cuando la BD está actualizada,
    o una lista de diccionarios basada en `User` si falta la columna (migraciones pendientes).
    Esto evita que las vistas y plantillas rompan antes de aplicar `makemigrations`/`migrate`.
    """
    try:
        return Usuario.objects.filter(user__is_staff=False).order_by('nombre')
    except OperationalError:
        users = User.objects.filter(is_staff=False).order_by('username')
        return [
            {'id': u.id, 'nombre': u.username, 'email': u.email or '', 'tel': ''}
            for u in users
        ]


def _safe_all_usuarios():
    """Devuelve todos los usuarios de tipo `Usuario` o una lista basada en `User` como fallback."""
    try:
        return Usuario.objects.all()
    except OperationalError:
        users = User.objects.all().order_by('username')
        return [
            {'id': u.id, 'nombre': u.username, 'email': u.email or '', 'tel': ''}
            for u in users
        ]


# ----------------------
# Panel de administración
# ----------------------
@login_required
@user_passes_test(is_staff_user)
def inicio_axolotlmusic(request):
    try:
        clientes_count = Usuario.objects.count()
    except OperationalError:
        clientes_count = User.objects.filter(is_staff=False).count()
    artistas_count = Artista.objects.count()
    productos_count = Producto.objects.count()
    pedidos_count = Pedido.objects.count()
    context = {
        'clientes_count': clientes_count,
        'artistas_count': artistas_count,
        'productos_count': productos_count,
        'pedidos_count': pedidos_count,
    }
    return render(request, 'admin_panel/dashboard.html', context)


# ----------------------
# CRUD Productos (Admin)
# ----------------------
@login_required
@user_passes_test(is_staff_user)
def agregar_productos(request):
    if request.method == 'POST':
        form = ProductoForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, 'Producto agregado correctamente.')
            return redirect('ver_productos')
    else:
        form = ProductoForm()
    return render(request, 'admin_panel/productos_agregar.html', {'form': form})


@login_required
@user_passes_test(is_staff_user)
def ver_productos(request):
    productos = Producto.objects.select_related('artista').all().order_by('-id')
    return render(request, 'admin_panel/productos_ver.html', {'productos': productos})


@login_required
@user_passes_test(is_staff_user)
def actualizar_productos(request, producto_id):
    producto = get_object_or_404(Producto, id=producto_id)
    if request.method == 'POST':
        form = ProductoForm(request.POST, request.FILES, instance=producto)
        if form.is_valid():
            form.save()
            messages.success(request, 'Producto actualizado correctamente.')
            return redirect('ver_productos')
    else:
        form = ProductoForm(instance=producto)
    return render(request, 'admin_panel/productos_actualizar.html', {'form': form, 'producto': producto})


@login_required
@user_passes_test(is_staff_user)
def borrar_productos(request, producto_id):
    producto = get_object_or_404(Producto, id=producto_id)
    if request.method == 'POST':
        producto.delete()
        messages.success(request, 'Producto eliminado.')
        return redirect('ver_productos')
    return render(request, 'admin_panel/productos_borrar.html', {'producto': producto})


# ----------------------
# CRUD Artistas (Admin)
# ----------------------
@login_required
@user_passes_test(is_staff_user)
def agregar_artistas(request):
    if request.method == 'POST':
        form = ArtistaForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, 'Artista agregado.')
            return redirect('ver_artistas')
    else:
        form = ArtistaForm()
    return render(request, 'artistas_admin/agregar_artistas.html', {'form': form})


@login_required
@user_passes_test(is_staff_user)
def ver_artistas(request):
    artistas = Artista.objects.all().order_by('nombre_artista')
    return render(request, 'artistas_admin/ver_artistas.html', {'artistas': artistas})


@login_required
@user_passes_test(is_staff_user)
def ver_clientes(request):
    # Mostrar solo usuarios que NO son staff/administradores
    clientes = _safe_clientes_list()
    return render(request, 'admin_panel/clientes_ver.html', {'clientes': clientes})


@login_required
@user_passes_test(is_staff_user)
def actualizar_cliente(request, cliente_id):
    cliente = get_object_or_404(Usuario, id=cliente_id)
    if request.method == 'POST':
        form = UsuarioForm(request.POST, instance=cliente)
        if form.is_valid():
            form.save()
            messages.success(request, 'Cliente actualizado.')
            return redirect('ver_clientes')
    else:
        form = UsuarioForm(instance=cliente)
    return render(request, 'admin_panel/clientes_actualizar.html', {'form': form, 'cliente': cliente})


@login_required
@user_passes_test(is_staff_user)
def borrar_cliente(request, cliente_id):
    cliente = get_object_or_404(Usuario, id=cliente_id)
    if request.method == 'POST':
        cliente.delete()
        messages.success(request, 'Cliente eliminado.')
        return redirect('ver_clientes')
    return render(request, 'admin_panel/clientes_borrar.html', {'cliente': cliente})


# ----------------------
# CRUD Empleados (Admin)
# ----------------------
@login_required
@user_passes_test(is_staff_user)
def ver_empleados(request):
    empleados = User.objects.filter(groups__name='Empleados') | User.objects.filter(is_staff=True)
    empleados = empleados.distinct().order_by('username')
    return render(request, 'admin_panel/empleados_ver.html', {'empleados': empleados})


@login_required
@user_passes_test(is_staff_user)
def agregar_empleado(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            new_user = form.save()
            # asignar al grupo Empleados (crear si no existe)
            group, _ = Group.objects.get_or_create(name='Empleados')
            new_user.groups.add(group)
            # marcar staff si viene marcado
            if request.POST.get('is_staff') == 'on':
                new_user.is_staff = True
                new_user.save()
            messages.success(request, 'Empleado creado correctamente.')
            return redirect('ver_empleados')
    else:
        form = UserCreationForm()
    return render(request, 'admin_panel/empleados_form.html', {'form': form, 'user_obj': None})


@login_required
@user_passes_test(is_staff_user)
def actualizar_empleado(request, empleado_id):
    user_obj = get_object_or_404(User, id=empleado_id)
    if request.method == 'POST':
        # solo permitir cambiar email y staff flag aquí
        user_obj.email = request.POST.get('email', user_obj.email)
        user_obj.is_staff = True if request.POST.get('is_staff') == 'on' else False
        user_obj.save()
        messages.success(request, 'Empleado actualizado.')
        return redirect('ver_empleados')
    # Create a minimal form-like object for template rendering (we'll use UserCreationForm for adding only)
    form = None
    return render(request, 'admin_panel/empleados_form.html', {'form': form, 'user_obj': user_obj})


@login_required
@user_passes_test(is_staff_user)
def borrar_empleado(request, empleado_id):
    user_obj = get_object_or_404(User, id=empleado_id)
    if request.method == 'POST':
        user_obj.delete()
        messages.success(request, 'Empleado eliminado.')
        return redirect('ver_empleados')
    return render(request, 'admin_panel/empleados_borrar.html', {'user_obj': user_obj})


@login_required
@user_passes_test(is_staff_user)
def actualizar_artistas(request, artista_id):
    artista = get_object_or_404(Artista, id=artista_id)
    if request.method == 'POST':
        form = ArtistaForm(request.POST, request.FILES, instance=artista)
        if form.is_valid():
            form.save()
            messages.success(request, 'Artista actualizado.')
            return redirect('ver_artistas')
    else:
        form = ArtistaForm(instance=artista)
    return render(request, 'artistas_admin/actualizar_artistas.html', {'form': form, 'artista': artista})


@login_required
@user_passes_test(is_staff_user)
def borrar_artistas(request, artista_id):
    artista = get_object_or_404(Artista, id=artista_id)
    if request.method == 'POST':
        artista.delete()
        messages.success(request, 'Artista eliminado.')
        return redirect('ver_artistas')
    return render(request, 'artistas_admin/borrar_artistas.html', {'artista': artista})


# ----------------------
# Vistas Frontend (cliente)
# ----------------------
def index_frontend(request):
    # Mostrar novedades y artistas como ejemplo
    novedades = Producto.objects.filter(novedad=True).order_by('-id')[:8]
    artistas = Artista.objects.all().order_by('nombre_artista')
    return render(request, 'index_frontend.html', {'novedades': novedades, 'artistas': artistas})


def artistas_frontend(request):
    artistas_db = Artista.objects.all().order_by('nombre_artista')
    artistas_por_letra = {}
    for artista in artistas_db:
        inicial = artista.nombre_artista[0].upper()
        artistas_por_letra.setdefault(inicial, []).append(artista)

    alfabeto = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    artistas_final = {letra: artistas_por_letra.get(letra, []) for letra in alfabeto}
    return render(request, 'artistas_frontend.html', {'artistas_por_letra': artistas_final})


def lista_frontend(request):
    """Página simplificada de lista de artistas. Se actualizará automáticamente al agregar artistas en admin."""
    artistas = Artista.objects.all().order_by('nombre_artista')
    return render(request, 'lista.html', {'artistas': artistas})


def comprar_frontend(request):
    artista_nombre = request.GET.get('artista')
    if not artista_nombre:
        return redirect('artistas_frontend')

    artista_obj = get_object_or_404(Artista, nombre_artista=artista_nombre)
    productos = Producto.objects.filter(artista=artista_obj)
    vinilos = productos.filter(tipo__iexact='vinilo')
    cds = productos.filter(tipo__iexact='cd')
    cassettes = productos.filter(tipo__iexact='casete')

    context = {
        'artista': artista_obj,
        'vinilos': vinilos,
        'cds': cds,
        'cassettes': cassettes,
    }
    return render(request, 'comprar.html', context)


def genero_frontend(request):
    genero_param = request.GET.get('genero')
    if not genero_param:
        productos = Producto.objects.all().order_by('nombre_producto')
        genero_nombre = "Todos los Géneros"
    else:
        productos = Producto.objects.filter(genero__iexact=genero_param).order_by('nombre_producto')
        genero_nombre = genero_param

    vinilos = productos.filter(tipo__iexact='vinilo')
    cds = productos.filter(tipo__iexact='cd')
    cassettes = productos.filter(tipo__iexact='casete')

    context = {
        'genero_nombre': genero_nombre,
        'vinilos': vinilos,
        'cds': cds,
        'cassettes': cassettes,
    }
    return render(request, 'genero.html', context)


def tipo_frontend(request):
    """Página para filtrar productos por tipo (Vinilo, CD, Casete)."""
    tipo_param = request.GET.get('tipo', 'Vinilo')
    
    # Filtrar por tipo
    productos = Producto.objects.filter(tipo__iexact=tipo_param).order_by('nombre_producto')
    
    # Agrupar por artista
    productos_por_artista = {}
    for producto in productos:
        artista_nombre = producto.artista.nombre_artista
        if artista_nombre not in productos_por_artista:
            productos_por_artista[artista_nombre] = []
        productos_por_artista[artista_nombre].append(producto)
    
    tipo_nombre = tipo_param.capitalize()
    
    context = {
        'tipo_nombre': tipo_nombre,
        'tipo_param': tipo_param,
        'productos_por_artista': productos_por_artista,
        'todos_productos': productos,
    }
    return render(request, 'tipo.html', context)


def novedades_frontend(request):
    novedades = Producto.objects.filter(novedad=True).order_by('-id')[:4]
    return render(request, 'novedades.html', {'novedades': novedades})


def catalogo_frontend(request):
    """Página que muestra todos los productos en orden alfabético.
    Diseño pensado como catálogo musical con estilo rosa/negro/blanco y referencias a ajolotes.
    """
    # Ordenar por género -> tipo -> artista -> nombre para agrupar por géneros
    productos_qs = Producto.objects.select_related('artista').all().order_by('genero', 'tipo', 'artista__nombre_artista', 'nombre_producto')

    # Agrupar por género manteniendo el orden
    productos_por_genero = {}
    for p in productos_qs:
        genero = p.genero or 'Sin género'
        productos_por_genero.setdefault(genero, []).append(p)

    return render(request, 'catalogo.html', {'productos_por_genero': productos_por_genero, 'productos': productos_qs})


def finalizar_frontend(request):
    artista_nombre = request.GET.get('artista')
    producto_nombre = request.GET.get('producto')
    precio = request.GET.get('precio')
    # Si el usuario está autenticado, intentar obtener su carrito para pasar totales reales
    cart_total = None
    cart_quantity = None
    cart_exists = False
    if request.user.is_authenticated:
        try:
            usuario = request.user.usuario
            cart = Cart.objects.filter(usuario=usuario).first()
            if cart and cart.items.exists():
                cart_exists = True
                items = cart.items.select_related('producto').all()
                cart_quantity = sum(i.cantidad for i in items)
                cart_total = sum(i.subtotal() for i in items)
        except Exception:
            pass

    context = {
        'artista': artista_nombre,
        'producto': producto_nombre,
        'precio': precio,
        'cart_total': cart_total,
        'cart_quantity': cart_quantity,
        'cart_exists': cart_exists,
    }
    return render(request, 'finalizar.html', context)


def gracias_frontend(request):
    # Página de agradecimiento. Si se recibe ?pedido=<id> mostrar resumen del pedido
    pedido_obj = None
    pedido_id = request.GET.get('pedido')
    if pedido_id:
        try:
            pedido_obj = Pedido.objects.select_related('usuario').get(id=int(pedido_id))
        except Exception:
            pedido_obj = None
    # Generar un código de seguimiento simple (no se guarda en BD)
    tracking = None
    if pedido_obj:
        try:
            tracking = f"TRK{int(pedido_obj.id):06d}"
        except Exception:
            tracking = None

    context = {'pedido': pedido_obj, 'tracking': tracking}
    return render(request, 'gracias.html', context)


def crear_pedido_publico(request):
    """Crear un Pedido a partir del formulario público (finalizar). No requiere autenticación.
    Busca o crea un `Usuario` por email, crea `Pedido` y (si existe) un `DetallePedido`.
    """
    if request.method != 'POST':
        return redirect('finalizar_frontend')

    nombre = request.POST.get('nombre', '').strip()
    direccion = request.POST.get('direccion', '').strip()
    email = request.POST.get('email', '').strip()
    metodo = request.POST.get('metodo', '').strip()
    artista_nombre = request.POST.get('artista', '').strip()
    producto_nombre = request.POST.get('producto', '').strip()
    precio_raw = request.POST.get('precio', '').strip()

    # Obtener o crear usuario (perfil) por email
    usuario = None
    if request.user.is_authenticated:
        try:
            usuario = request.user.usuario
            # actualizar datos públicos si vienen
            if nombre:
                usuario.nombre = nombre
            if direccion:
                usuario.direccion = direccion
            if email:
                usuario.email = email
            usuario.save()
        except Exception:
            usuario = None

    if not usuario:
        if email:
            try:
                usuario = Usuario.objects.get(email=email)
                if nombre:
                    usuario.nombre = nombre
                if direccion:
                    usuario.direccion = direccion
                usuario.save()
            except Usuario.DoesNotExist:
                usuario = Usuario.objects.create(nombre=nombre or email, email=email, direccion=direccion)
        else:
            usuario = Usuario.objects.create(nombre=nombre or 'Cliente anónimo', email=f'anon_{Pedido.objects.count()+1}@local')

    # Si el usuario tiene un carrito con items, usar esos valores reales
    try:
        cart = Cart.objects.filter(usuario=usuario).first()
    except Exception:
        cart = None

    if cart and cart.items.exists():
        items = list(cart.items.select_related('producto').all())
        # Proteger la operación con transacción y bloqueos para evitar race conditions
        product_ids = [i.producto.id for i in items]
        try:
            with transaction.atomic():
                productos_locked = Producto.objects.select_for_update().filter(id__in=product_ids)
                producto_map = {p.id: p for p in productos_locked}

                # Re-verificar stock después de bloquear filas
                for i in items:
                    p = producto_map.get(i.producto.id)
                    if not p or p.stock <= 0:
                        messages.error(request, f'El producto "{i.producto.nombre_producto}" está fuera de stock.')
                        return redirect('ver_carrito')
                    if i.cantidad > p.stock:
                        messages.error(request, f'Solo quedan {p.stock} unidades de "{i.producto.nombre_producto}" en stock.')
                        return redirect('ver_carrito')

                cantidad_total = sum(i.cantidad for i in items)
                total = sum(i.subtotal() for i in items)

                pedido = Pedido.objects.create(usuario=usuario, cantidad_producto=cantidad_total, total=total)

                for i in items:
                    DetallePedido.objects.create(
                        pedido=pedido,
                        usuario=usuario,
                        producto=i.producto,
                        cantidad_producto=i.cantidad,
                        precio=i.producto.precio,
                        total=i.subtotal()
                    )

                    # Reducir stock del producto vendido (usando la instancia bloqueada)
                    try:
                        p_locked = producto_map.get(i.producto.id)
                        if p_locked:
                            p_locked.stock = max(0, p_locked.stock - i.cantidad)
                            p_locked.save()
                    except Exception:
                        pass

                # limpiar carrito
                try:
                    cart.items.all().delete()
                except Exception:
                    pass

                return redirect(f"{reverse('gracias_frontend')}?cleared=1&pedido={pedido.id}")
        except Exception:
            messages.error(request, 'Error procesando el pedido. Intenta de nuevo.')
            return redirect('ver_carrito')

    # Si no hay carrito, usar los datos enviados (cantidad y precio)
    import re
    cantidad = int(request.POST.get('cantidad', '1') or '1')
    price_clean = re.sub(r'[^0-9.,]', '', precio_raw).replace(',', '.')
    try:
        unit_price = float(price_clean) if price_clean else 0.0
    except Exception:
        unit_price = 0.0

    total = unit_price * cantidad

    pedido = Pedido.objects.create(usuario=usuario, cantidad_producto=cantidad, total=total)

    # Intentar enlazar un Producto existente y crear DetallePedido con cantidad
    producto_obj = None
    if producto_nombre:
        qs = Producto.objects.filter(nombre_producto__iexact=producto_nombre)
        if artista_nombre:
            qs = qs.filter(artista__nombre_artista__iexact=artista_nombre)
        producto_obj = qs.first()

    if producto_obj:
        # Verificar stock para compra individual
        if producto_obj.stock <= 0:
            messages.error(request, f'El producto "{producto_obj.nombre_producto}" está fuera de stock.')
            return redirect(f"{reverse('finalizar_frontend')}?artista={artista_nombre}&producto={producto_nombre}&precio={precio_raw}")
        if cantidad > producto_obj.stock:
            messages.error(request, f'Solo quedan {producto_obj.stock} unidades de "{producto_obj.nombre_producto}" en stock.')
            return redirect(f"{reverse('finalizar_frontend')}?artista={artista_nombre}&producto={producto_nombre}&precio={precio_raw}")

        DetallePedido.objects.create(
            pedido=pedido,
            usuario=usuario,
            producto=producto_obj,
            cantidad_producto=cantidad,
            precio=producto_obj.precio,
            total=total,
        )

        # Reducir stock del producto vendido
        try:
            producto_obj.stock = max(0, producto_obj.stock - cantidad)
            producto_obj.save()
        except Exception:
            pass

    return redirect(f"{reverse('gracias_frontend')}?cleared=1&pedido={pedido.id}")


# ----------------------
# CARRITO (cliente)
# ----------------------
@login_required
def add_to_cart(request, producto_id):
    producto = get_object_or_404(Producto, id=producto_id)
    usuario = request.user.usuario
    cart, _ = Cart.objects.get_or_create(usuario=usuario)

    # cantidad desde POST (si no viene, 1)
    cantidad = int(request.POST.get('cantidad', 1)) if request.method == 'POST' else 1
    # Validar stock antes de agregar
    if producto.stock <= 0:
        messages.error(request, f'"{producto.nombre_producto}" está fuera de stock.')
        next_url = request.POST.get('next') or request.META.get('HTTP_REFERER') or '/index/'
        return redirect(next_url)

    item, created = CartItem.objects.get_or_create(cart=cart, producto=producto)
    current_qty = item.cantidad if not created else 0
    requested_new = current_qty + cantidad

    if requested_new > producto.stock:
        messages.error(request, f'No se pueden agregar {cantidad} unidades. Solo quedan {producto.stock - current_qty} unidades de "{producto.nombre_producto}".')
        next_url = request.POST.get('next') or request.META.get('HTTP_REFERER') or '/index/'
        return redirect(next_url)

    # Aplicar la suma segura
    if not created:
        item.cantidad = current_qty + cantidad
    else:
        item.cantidad = cantidad
    item.save()

    messages.success(request, f'"{producto.nombre_producto}" agregado al carrito.')
    # redirigir a la página anterior o al index
    next_url = request.POST.get('next') or request.META.get('HTTP_REFERER') or '/index/'
    return redirect(next_url)


@login_required
def ver_carrito(request):
    usuario = request.user.usuario
    cart, _ = Cart.objects.get_or_create(usuario=usuario)
    items = cart.items.select_related('producto').all()
    total = sum(item.subtotal() for item in items)
    # Detectar si hay problemas de stock en el carrito
    cart_has_stock_issue = any((item.producto.stock <= 0) or (item.cantidad > item.producto.stock) for item in items)
    return render(request, 'cart.html', {'cart': cart, 'items': items, 'total': total, 'cart_has_stock_issue': cart_has_stock_issue})


@login_required
def update_cart_item(request, item_id):
    item = get_object_or_404(CartItem, id=item_id, cart__usuario__user=request.user)
    if request.method == 'POST':
        try:
            cantidad = int(request.POST.get('cantidad', 1))
            # Validar stock disponible
            if cantidad <= 0:
                item.delete()
            else:
                if cantidad > item.producto.stock:
                    messages.error(request, f'Solo quedan {item.producto.stock} unidades de "{item.producto.nombre_producto}" en stock.')
                    return redirect('ver_carrito')
                item.cantidad = cantidad
                item.save()
            messages.success(request, 'Carrito actualizado.')
        except Exception:
            messages.error(request, 'Error al actualizar la cantidad.')
    return redirect('ver_carrito')


@login_required
def remove_cart_item(request, item_id):
    item = get_object_or_404(CartItem, id=item_id, cart__usuario__user=request.user)
    if request.method == 'POST':
        item.delete()
        messages.success(request, 'Producto eliminado del carrito.')
    return redirect('ver_carrito')


# ----------------------
# PERFIL DE USUARIO
# ----------------------
@login_required
def perfil_usuario(request):
    usuario = request.user.usuario
    pedidos = usuario.pedidos.order_by('-fecha')[:20]
    return render(request, 'perfil.html', {'usuario': usuario, 'pedidos': pedidos})


@login_required
def editar_perfil(request):
    usuario = request.user.usuario
    if request.method == 'POST':
        form = UsuarioForm(request.POST, request.FILES, instance=usuario)
        if form.is_valid():
            form.save()
            messages.success(request, 'Perfil actualizado.')
            return redirect('perfil_usuario')
    else:
        form = UsuarioForm(instance=usuario)
    return render(request, 'perfil_editar.html', {'form': form})


# ----------------------
# CRUD Pedidos (Admin)
# ----------------------
@login_required
@user_passes_test(is_staff_user)
def ver_pedidos(request):
    pedidos = Pedido.objects.select_related('usuario').all().order_by('-fecha')
    return render(request, 'admin_panel/pedidos_ver.html', {'pedidos': pedidos})


@login_required
@user_passes_test(is_staff_user)
def agregar_pedido(request):
    if request.method == 'POST':
        usuario_id = request.POST.get('usuario')
        cantidad_producto = request.POST.get('cantidad_producto')
        total = request.POST.get('total')
        
        try:
            usuario = Usuario.objects.get(id=usuario_id)
            pedido = Pedido.objects.create(
                usuario=usuario,
                cantidad_producto=int(cantidad_producto),
                total=float(total)
            )
            messages.success(request, 'Pedido creado correctamente.')
            return redirect('ver_pedidos')
        except Exception as e:
            messages.error(request, f'Error al crear pedido: {str(e)}')
            
    usuarios = _safe_all_usuarios()
    return render(request, 'admin_panel/pedidos_agregar.html', {'usuarios': usuarios})


@login_required
@user_passes_test(is_staff_user)
def actualizar_pedido(request, pedido_id):
    pedido = get_object_or_404(Pedido, id=pedido_id)
    if request.method == 'POST':
        pedido.cantidad_producto = int(request.POST.get('cantidad_producto', pedido.cantidad_producto))
        pedido.total = float(request.POST.get('total', pedido.total))
        pedido.save()
        messages.success(request, 'Pedido actualizado correctamente.')
        return redirect('ver_pedidos')
    
    usuarios = _safe_all_usuarios()
    return render(request, 'admin_panel/pedidos_actualizar.html', {'pedido': pedido, 'usuarios': usuarios})


@login_required
@user_passes_test(is_staff_user)
def borrar_pedido(request, pedido_id):
    pedido = get_object_or_404(Pedido, id=pedido_id)
    if request.method == 'POST':
        pedido.delete()
        messages.success(request, 'Pedido eliminado.')
        return redirect('ver_pedidos')
    return render(request, 'admin_panel/pedidos_borrar.html', {'pedido': pedido})


# ----------------------
# CRUD Detalles Pedidos (Admin)
# ----------------------
@login_required
@user_passes_test(is_staff_user)
def ver_detalles_pedidos(request):
    detalles = DetallePedido.objects.select_related('pedido', 'usuario', 'producto').all().order_by('-fecha')
    return render(request, 'admin_panel/detalles_pedidos_ver.html', {'detalles': detalles})


@login_required
@user_passes_test(is_staff_user)
def agregar_detalle_pedido(request):
    if request.method == 'POST':
        pedido_id = request.POST.get('pedido')
        usuario_id = request.POST.get('usuario')
        producto_id = request.POST.get('producto')
        cantidad_producto = request.POST.get('cantidad_producto')
        precio = request.POST.get('precio')
        total = request.POST.get('total')
        
        try:
            pedido = Pedido.objects.get(id=pedido_id)
            usuario = Usuario.objects.get(id=usuario_id)
            producto = Producto.objects.get(id=producto_id)
            
            detalle = DetallePedido.objects.create(
                pedido=pedido,
                usuario=usuario,
                producto=producto,
                cantidad_producto=int(cantidad_producto),
                precio=float(precio),
                total=float(total)
            )
            messages.success(request, 'Detalle de pedido creado correctamente.')
            return redirect('ver_detalles_pedidos')
        except Exception as e:
            messages.error(request, f'Error al crear detalle: {str(e)}')
            
    pedidos = Pedido.objects.all()
    usuarios = _safe_all_usuarios()
    productos = Producto.objects.all()
    return render(request, 'admin_panel/detalles_pedidos_agregar.html', {
        'pedidos': pedidos,
        'usuarios': usuarios,
        'productos': productos
    })


@login_required
@user_passes_test(is_staff_user)
def actualizar_detalle_pedido(request, detalle_id):
    detalle = get_object_or_404(DetallePedido, id=detalle_id)
    if request.method == 'POST':
        detalle.cantidad_producto = int(request.POST.get('cantidad_producto', detalle.cantidad_producto))
        detalle.precio = float(request.POST.get('precio', detalle.precio))
        detalle.total = float(request.POST.get('total', detalle.total))
        detalle.save()
        messages.success(request, 'Detalle actualizado correctamente.')
        return redirect('ver_detalles_pedidos')
    
    pedidos = Pedido.objects.all()
    usuarios = _safe_all_usuarios()
    productos = Producto.objects.all()
    return render(request, 'admin_panel/detalles_pedidos_actualizar.html', {
        'detalle': detalle,
        'pedidos': pedidos,
        'usuarios': usuarios,
        'productos': productos
    })


@login_required
@user_passes_test(is_staff_user)
def borrar_detalle_pedido(request, detalle_id):
    detalle = get_object_or_404(DetallePedido, id=detalle_id)
    if request.method == 'POST':
        detalle.delete()
        messages.success(request, 'Detalle de pedido eliminado.')
        return redirect('ver_detalles_pedidos')
    return render(request, 'admin_panel/detalles_pedidos_borrar.html', {'detalle': detalle})