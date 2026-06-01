# Material Management API

A FastAPI-based REST API for restaurant ERP material and inventory management with forecasting capabilities.

## Project Structure

```
.
├── app/                    # Main application package
│   ├── __init__.py
│   ├── main.py            # FastAPI application entry point
│   ├── database.py        # Database configuration
│   ├── models/            # SQLAlchemy models
│   ├── routes/            # API routes
│   ├── schemas/           # Pydantic schemas
│   └── services/          # Business logic services
├── config/                # Configuration files
│   ├── nginx.conf         # Nginx reverse proxy configuration
│   └── systemd.service    # Systemd service file
├── logs/                  # Application logs
├── Dockerfile             # Docker image definition
├── docker-compose.yml     # Docker Compose configuration
├── gunicorn_config.py     # Gunicorn WSGI server configuration
├── requirements.txt       # Python dependencies
├── run.py                 # Application entry point
├── .env.example           # Environment variables template
└── README.md              # This file
```

## Prerequisites

- Python 3.11+
- MySQL 8.0+
- Docker & Docker Compose (optional, for containerized deployment)
- Nginx (for reverse proxy in production)

## Installation

### Local Development

1. **Clone the repository**
   ```bash
   git clone <your-repo-url>
   cd Material-Management/python
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment**
   ```bash
   cp .env.example .env
   # Edit .env with your database credentials
   ```

5. **Run development server**
   ```bash
   python run.py
   ```

   The API will be available at `http://localhost:8000`

## Deployment

### Docker Deployment

1. **Configure environment**
   ```bash
   cp .env.example .env
   # Edit .env with production values
   ```

2. **Build and run with Docker Compose**
   ```bash
   docker-compose up -d
   ```

3. **Verify deployment**
   ```bash
   docker-compose ps
   curl http://localhost:8000
   ```

### VPS Deployment (Manual)

1. **SSH into your VPS**
   ```bash
   ssh user@your-vps-ip
   ```

2. **Clone and setup**
   ```bash
   cd /opt
   git clone <your-repo-url> material-management-api
   cd material-management-api
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   cp .env.example .env
   # Edit .env with production values
   ```

3. **Setup Systemd service**
   ```bash
   sudo cp config/systemd.service /etc/systemd/system/material-management-api.service
   sudo systemctl daemon-reload
   sudo systemctl enable material-management-api
   sudo systemctl start material-management-api
   ```

4. **Setup Nginx reverse proxy**
   ```bash
   sudo cp config/nginx.conf /etc/nginx/sites-available/material-management-api
   sudo ln -s /etc/nginx/sites-available/material-management-api /etc/nginx/sites-enabled/
   sudo nginx -t
   sudo systemctl restart nginx
   ```

5. **Setup SSL with Let's Encrypt** (optional)
   ```bash
   sudo apt-get install certbot python3-certbot-nginx
   sudo certbot --nginx -d your-domain.com
   ```

## API Documentation

Once running, visit:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI Schema**: http://localhost:8000/openapi.json

## Configuration

### Environment Variables

See `.env.example` for all available configuration options:

- `APP_ENV`: Application environment (development/production)
- `APP_HOST`: Bind address (default: 0.0.0.0)
- `APP_PORT`: Bind port (default: 8000)
- `DEV_DB_*`: Database connection parameters
- `WORKERS`: Number of Gunicorn workers (default: CPU count × 2 + 1)

## Monitoring & Logs

- **Application logs**: `logs/app.log`
- **Error logs**: `logs/error.log`
- **System logs** (Systemd): `sudo journalctl -u material-management-api -f`

## Development

### Adding new routes
Create new route files in `app/routes/` and include them in `app/main.py`:

```python
from app.routes.your_routes import router as your_router
app.include_router(your_router, prefix="/api/your-prefix", tags=["Your Tag"])
```

### Database models
Define new models in `app/models/` and ensure they inherit from `Base`.

### API schemas
Define request/response schemas in `app/schemas/` using Pydantic.

## Troubleshooting

### Database connection issues
- Ensure MySQL is running and accessible
- Check `.env` database credentials
- Verify firewall rules allow MySQL port (3306)

### Port already in use
```bash
# Find process using port 8000
lsof -i :8000
# Kill the process
kill -9 <PID>
```

### Permission denied errors
Ensure proper permissions:
```bash
sudo chown -R www-data:www-data /opt/material-management-api
sudo chmod -R 755 /opt/material-management-api
```

## Performance Optimization

- Increase `WORKERS` for high-traffic scenarios
- Use CDN for static files
- Enable Nginx caching for read-heavy endpoints
- Monitor with `htop`, `iostat`, `vmstat`

## Security

- Always use HTTPS in production
- Keep dependencies updated: `pip install --upgrade -r requirements.txt`
- Use strong database passwords
- Implement rate limiting (add middleware if needed)
- Regular backups of MySQL database

## License

[Your License Here]

## Support

For issues and questions, please contact the development team.
