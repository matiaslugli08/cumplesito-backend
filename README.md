# 🎂 Cumplesito - Backend API

> API REST para gestión de listas de deseos de cumpleaños

## 🚀 Características

- 🔐 **Autenticación JWT**: Sistema seguro de login y registro
- 📝 **CRUD Completo**: Gestión de usuarios, listas y productos
- 🌐 **CORS Configurado**: Listo para frontend en cualquier dominio
- 🔍 **Web Scraping**: Extracción automática de metadata de productos
- 🛡️ **Validación**: Schemas con Pydantic
- 📊 **Base de Datos**: PostgreSQL con SQLAlchemy ORM
- 📚 **Documentación**: Swagger UI automática en `/docs`
- 🎯 **MercadoLibre**: Soporte especializado para productos

## 🛠️ Tecnologías

- **FastAPI** - Framework web moderno
- **SQLAlchemy** - ORM para base de datos
- **PostgreSQL** - Base de datos
- **Pydantic** - Validación de datos
- **JWT** - Autenticación
- **BeautifulSoup** - Web scraping
- **Uvicorn** - Servidor ASGI

## 📦 Instalación

```bash
# Crear entorno virtual
python -m venv venv

# Activar entorno virtual
# macOS/Linux:
source venv/bin/activate
# Windows:
venv\Scripts\activate

# Instalar dependencias
pip install -r requirements.txt

# Copiar variables de entorno
cp .env.example .env
```

## ⚙️ Configuración

Edita el archivo `.env`:

```env
# Database
DATABASE_URL=postgresql://usuario:password@localhost:5432/cumplesito_db

# JWT
SECRET_KEY=tu-clave-secreta-super-segura-aqui
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=43200

# CORS
BACKEND_CORS_ORIGINS=http://localhost:5173,http://localhost:3000
```

## 🗄️ Base de Datos

```bash
# Crear base de datos en PostgreSQL
createdb cumplesito_db

# Las tablas se crean automáticamente al iniciar la app
```

## 🏃 Desarrollo

```bash
# Iniciar servidor de desarrollo
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# O usar el script directo
python -m uvicorn app.main:app --reload
```

La API estará disponible en:
- **API**: http://localhost:8000
- **Docs**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## 📚 Documentación API

### Endpoints Principales

#### Autenticación
- `POST /api/auth/register` - Registrar usuario
- `POST /api/auth/login` - Iniciar sesión

#### Listas de Deseos
- `GET /api/wishlists` - Listar todas las listas
- `POST /api/wishlists` - Crear lista
- `GET /api/wishlists/{id}` - Obtener lista por ID
- `PUT /api/wishlists/{id}` - Actualizar lista
- `DELETE /api/wishlists/{id}` - Eliminar lista

#### Items de Lista
- `POST /api/wishlists/{id}/items` - Agregar item
- `PUT /api/items/{id}` - Actualizar item
- `DELETE /api/items/{id}` - Eliminar item
- `POST /api/items/{id}/purchase` - Marcar como comprado

#### Metadata
- `POST /api/metadata/extract` - Extraer metadata de URL

## 📁 Estructura del Proyecto

```
app/
├── routers/        # Endpoints de la API
├── models/         # Modelos de base de datos
├── schemas/        # Schemas de Pydantic
├── utils/          # Utilidades (scraping, etc)
├── config.py       # Configuración
├── database.py     # Conexión a BD
└── main.py         # Aplicación principal
```

## 🔒 Seguridad

- Contraseñas hasheadas con bcrypt
- JWT con expiración configurable
- CORS configurado
- Validación de datos con Pydantic

## 🌐 Web Scraping

El backend incluye capacidades de web scraping para:
- Extraer títulos de productos
- Obtener imágenes
- Detectar descripciones
- Extraer precios

**Nota sobre MercadoLibre**: Ver `MERCADOLIBRE_INFO.md` para detalles sobre limitaciones.

## 🚀 Deploy

### Heroku

```bash
# Login
heroku login

# Crear app
heroku create cumplesito-api

# Agregar PostgreSQL
heroku addons:create heroku-postgresql:mini

# Configurar variables
heroku config:set SECRET_KEY=tu-clave-secreta
heroku config:set BACKEND_CORS_ORIGINS=https://tu-frontend.com

# Deploy
git push heroku main
```

### Railway / Render

1. Conecta tu repositorio
2. Configura las variables de entorno
3. Agrega base de datos PostgreSQL
4. Deploy automático

## 📝 Licencia

MIT

## 👨‍💻 Autor

**Matias Lugli** - [GitHub](https://github.com/matiaslugli08)

---

Hecho con ❤️ para hacer los cumpleaños más especiales
