# BBQ App - Event Registration System

A modern, configurable web application for managing BBQ event registrations. Built with Flask and designed for easy deployment and customization.

## Features

- 🎯 **Configurable Event Details**: Set dates, locations, prices, and content through admin interface
- 📝 **Registration Form**: Collect participant information with dynamic pricing
- 💳 **Flexible Payment**: Support for Bunq.me integration or manual payment collection
- 📧 **Email Notifications**: Automatic confirmation emails to participants and organizers
- 🎨 **Customizable Design**: Configure colors, hero images, and content
- 📱 **Responsive Design**: Works perfectly on desktop and mobile devices
- 🔒 **Admin Interface**: Secure admin panel for managing all settings
- 📊 **Registration Management**: View and manage participant registrations

## Quick Start

### Option 1: Docker (Recommended)

1. **Clone the repository**
   ```bash
   git clone https://github.com/kay-arne/BBQ-App.git
   cd BBQ-App
   ```

2. **Configure environment**
   ```bash
   cp config.example .env
   # Edit .env with your settings (see Configuration section)
   ```

3. **Start with Docker Compose**
   ```bash
   docker-compose up -d
   ```

4. **Access the application**
   - Main site: http://localhost:3000
   - Admin panel: http://localhost:3000/admin
   - Default admin password: `change_this_strong_password` (change in .env)

### Option 2: Manual Installation

1. **Prerequisites**
   - Python 3.9+
   - pip

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment**
   ```bash
   cp config.example .env
   # Edit .env with your settings
   ```

4. **Run the application**
   ```bash
   python app.py
   ```

## Configuration

### Environment Variables (.env file)

#### Required Settings
- `SECRET_KEY`: A secure secret key for Flask sessions (generate a random string)
- `ADMIN_PASSWORD`: Password for admin access

#### Optional Settings
- `SMTP_SERVER`: SMTP server for sending emails (e.g., smtp.gmail.com)
- `SMTP_PORT`: SMTP port (usually 587)
- `SMTP_USERNAME`: Email username
- `SMTP_PASSWORD`: Email password or app password
- `ORGANIZER_EMAIL`: Email address for receiving registrations

### Admin Configuration

After first login, configure your event through the admin interface:

1. **Content Tab**: Set hero text, main content, and not-planned mode
2. **Variables Tab**: Configure BBQ details (date, location, prices)
3. **Benefits Tab**: Customize the 4 benefit cards
4. **Payment Tab**: Set up payment method (none or Bunq.me)
5. **Style Tab**: Customize colors and appearance
6. **Email Tab**: Configure email settings

## Docker Deployment

### Production Deployment

1. **Set up environment variables**
   ```bash
   export SECRET_KEY="your-very-secure-secret-key"
   export ADMIN_PASSWORD="your-secure-admin-password"
   ```

2. **Deploy with Docker Compose**
   ```bash
   docker-compose up -d
   ```

3. **Check logs**
   ```bash
   docker-compose logs -f
   ```

4. **Configure the application**
   - Access the admin panel at `http://localhost:3000/admin`
   - Login with your admin password
   - Configure BBQ details, email settings, and other options through the admin interface

### Custom Port

To run on a different port, modify `docker-compose.yml`:
```yaml
ports:
  - "8080:3000"  # Change 8080 to your desired port
```

### Database Persistence

**IMPORTANT**: The application uses Docker volumes to persist data:

- **`bbq_db`**: Contains the SQLite database (`bbq.db`) with all registrations and configuration
- **`bbq_data`**: Contains uploaded images and static files

These volumes ensure your data survives container restarts and updates. The database is automatically created on first run.

**Backup your data**:
```bash
# Backup the database
docker cp bbq-app_bbq-app_1:/app/bbq.db ./backup-bbq.db

# Backup uploaded files
docker cp bbq-app_bbq-app_1:/app/static/uploads ./backup-uploads
```

## Security Considerations

- **Change default passwords**: Always change the admin password
- **Use HTTPS**: Set up SSL/TLS in production
- **Secure email configuration**: Configure SMTP settings through the admin interface with app passwords
- **Regular updates**: Keep dependencies updated
- **Backup data**: Regular backups of the database and uploads (see Database Persistence section)
- **Security audit**: Run `pip-audit` to check for vulnerabilities
- **Dependency management**: Only necessary dependencies included

### Security Features
- ✅ SQL injection protection (parameterized queries)
- ✅ CSRF protection on all forms
- ✅ Input validation and sanitization
- ✅ Secure file upload handling
- ✅ Password hashing with Werkzeug
- ✅ Session management with configurable lifetime
- ✅ Non-root Docker container execution

## Performance Features

- 🚀 **Database Optimization**: Connection pooling, WAL mode, optimized indexes
- ⚡ **Caching**: LRU cache for configuration, static file caching
- 🔄 **Async Operations**: Non-blocking email processing
- 📊 **Resource Management**: Efficient memory usage and connection handling
- 🎯 **Production Ready**: Gunicorn WSGI server, health checks

## File Structure

```
BBQ-App/
├── app.py                 # Main application file
├── requirements.txt       # Python dependencies
├── Dockerfile            # Docker configuration
├── docker-compose.yml    # Docker Compose configuration
├── config.example        # Environment configuration template
├── static/               # Static files (CSS, JS, images)
│   ├── style.css
│   ├── script.js
│   └── uploads/          # User uploaded images
├── templates/            # HTML templates
│   ├── index.html        # Main registration page
│   ├── admin.html        # Admin dashboard
│   ├── admin_config.html # Configuration interface
│   ├── login.html        # Admin login
│   └── success.html      # Registration success page
└── bbq.db               # SQLite database (created automatically)
```

## Customization

### Adding New Configuration Options

1. Add to `initialize_default_config()` in `app.py`
2. Add form fields in `templates/admin_config.html`
3. Update the appropriate tab's category mapping

### Styling

- Modify `static/style.css` for custom styling
- Use CSS custom properties for easy color theming
- All colors are configurable through the admin interface

### Content

- All text content is configurable through the admin interface
- Supports HTML in content fields
- Variables like `{date}`, `{price}`, `{location}` are automatically replaced

## Troubleshooting

### Common Issues

1. **Database not created**: Ensure the app has write permissions in the directory
2. **Email not working**: Check SMTP settings and use app passwords for Gmail
3. **Images not uploading**: Check file permissions in `static/uploads/`
4. **Admin login issues**: Verify `ADMIN_PASSWORD` in .env file

### Logs

- Application logs: Check console output or Docker logs
- Database issues: Check file permissions for `bbq.db`
- Email issues: Verify SMTP credentials and network connectivity

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

This project is open source. Feel free to use and modify for your own BBQ events!

## Support

For issues and questions:
- Check the troubleshooting section
- Review the configuration options
- Open an issue on GitHub

---

**Happy BBQ organizing! 🍖🔥**
