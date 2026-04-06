# Plantilla Flask RGV

Plantilla base de RGV para aplicaciones web con Flask, incluyendo autenticación, control de acceso por roles, auditoría automática y funcionalidades comunes.

## Instalación rápida

### 1. Clonar y configurar entorno

```bash
git clone <url-del-repositorio>
cd Plantilla-Web-Apps-Flask
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configurar variables de entorno

```bash
cp .env.example .env
```

Edita `.env` con tus valores. Para generar las claves de seguridad:

```bash
# Generar ENCRYPTION_KEY
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"

# Generar SECRET_KEY
python -c "import secrets; print(secrets.token_hex(32))"
```

### 3. Configurar base de datos

```bash
psql -U postgres
CREATE DATABASE nombre_db;
\q
```

### 4. Ejecutar migraciones

```bash
flask db upgrade
```

### 5. Ejecutar aplicación

```bash
python app.py
```

La app estará en `http://localhost:8000`

## Variables de entorno requeridas

Variables mínimas en `.env`:

```bash
DB_NAME=tu_base_de_datos
DB_USER=postgres
DB_PASSWORD=tu_contraseña
DB_HOST=localhost
DB_PORT=5432
ENCRYPTION_KEY=generar_con_comando_arriba
SECRET_KEY=generar_con_comando_arriba
```

Ver `.env.example` para variables opcionales (email, WebAuthn, AWS S3).

## Comandos útiles

```bash
flask db migrate -m "mensaje"  # Nueva migración
flask db upgrade               # Aplicar migraciones
flask test                     # Ejecutar tests
flask shell                    # Shell interactivo
```

**Nota:** Nunca subas el archivo `.env` a git. Mantén tus credenciales seguras.
