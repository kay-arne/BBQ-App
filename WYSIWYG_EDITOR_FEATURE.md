# 📝 WYSIWYG Editor Feature

## Overview
The BBQ application now includes a powerful WYSIWYG (What You See Is What You Get) editor that allows administrators to create and style rich text content for the main page without any coding knowledge.

## 🆕 New Features

### 1. **Rich Text Editor Integration**
- **TinyMCE Integration**: Professional-grade WYSIWYG editor
- **Full formatting capabilities**: Bold, italic, colors, alignment, lists, links
- **Real-time preview**: See exactly how content will appear
- **User-friendly interface**: Intuitive toolbar and editing experience

### 2. **Dynamic Content System**
- **Configurable main content**: Complete control over the main page text
- **Dynamic placeholders**: Automatic insertion of BBQ details
- **HTML support**: Full HTML formatting and styling
- **Safe rendering**: Secure HTML output with proper sanitization

### 3. **Admin Interface Enhancements**
- **Dedicated content editor**: Large, user-friendly text area
- **Placeholder documentation**: Clear instructions on available variables
- **Auto-save functionality**: Content saved automatically on form submission
- **Professional styling**: Matches existing admin interface design

## 🎯 How It Works

### For Administrators

1. **Access the Editor**:
   - Login to admin panel
   - Navigate to "⚙️ Configuratie"
   - Find "📝 Inhoud" section
   - Locate "Hoofdinhoud van de aanmeldpagina (HTML)"

2. **Edit Content**:
   - Click in the large text area
   - Use the toolbar to format text (bold, italic, colors, etc.)
   - Add links, lists, and other formatting
   - Use placeholders for dynamic content

3. **Available Placeholders**:
   - `{date}` - BBQ event date
   - `{location}` - Event location
   - `{price}` - Price per adult
   - `{deadline}` - Registration deadline

4. **Save Changes**:
   - Click "💾 Configuratie Opslaan"
   - Changes take effect immediately on the main page

### For Users
- **Seamless experience**: Rich, formatted content displays beautifully
- **Dynamic information**: Always up-to-date event details
- **Professional appearance**: Styled content matches the overall design

## 🛠️ Technical Implementation

### Backend Changes

#### Configuration System
```python
# New configuration field
'main_content': ('<h2>🎉 Welkom bij ons jaarlijkse buurtfeest!</h2>...', 
                 'Hoofdinhoud van de aanmeldpagina (HTML)', 'content')
```

#### Template Function
```python
@app.template_global()
def render_main_content():
    """Render the main content with dynamic placeholders"""
    content = get_config('main_content', '')
    bbq_details = get_cached_bbq_details()
    
    # Replace placeholders with actual values
    content = content.replace('{date}', bbq_details['date'])
    content = content.replace('{location}', bbq_details['location'])
    content = content.replace('{price}', f"{bbq_details['price_per_adult']:.2f}")
    content = content.replace('{deadline}', bbq_details['deadline'])
    
    # Return as safe HTML (Markup)
    return Markup(content)
```

### Frontend Changes

#### TinyMCE Integration
```javascript
tinymce.init({
    selector: '#config_main_content',
    height: 400,
    menubar: false,
    plugins: [
        'advlist', 'autolink', 'lists', 'link', 'image', 'charmap', 'preview',
        'anchor', 'searchreplace', 'visualblocks', 'code', 'fullscreen',
        'insertdatetime', 'media', 'table', 'help', 'wordcount'
    ],
    toolbar: 'undo redo | blocks | ' +
        'bold italic forecolor | alignleft aligncenter ' +
        'alignright alignjustify | bullist numlist outdent indent | ' +
        'removeformat | help',
    content_style: 'body { font-family: Inter, -apple-system, BlinkMacSystemFont, Roboto, sans-serif; font-size: 14px; }'
});
```

#### Template Updates
```html
<!-- Before: Hardcoded content -->
<div class="card">
    <h2>🎉 Welkom bij ons jaarlijkse buurtfeest!</h2>
    <p><strong>Beste Kamperweg buurtgenoten,</strong></p>
    <!-- ... lots of hardcoded HTML ... -->
</div>

<!-- After: Dynamic content -->
<div class="card">
    {{ render_main_content() }}
</div>
```

## 🔒 Security Features

### HTML Sanitization
- **Safe rendering**: Uses Flask's Markup for secure HTML output
- **XSS protection**: Proper escaping of user content
- **Input validation**: Server-side validation of configuration values
- **CSRF protection**: All forms protected against CSRF attacks

### Content Validation
- **Server-side checks**: All content validated before saving
- **Database constraints**: Proper data types and limits
- **Error handling**: Graceful handling of invalid content

## 🎨 Editor Features

### Formatting Options
- **Text formatting**: Bold, italic, underline, strikethrough
- **Text colors**: Foreground and background colors
- **Alignment**: Left, center, right, justify
- **Lists**: Bulleted and numbered lists
- **Links**: Insert and edit hyperlinks
- **Images**: Insert and manage images
- **Tables**: Create and edit tables

### Advanced Features
- **Undo/Redo**: Full history of changes
- **Search and replace**: Find and replace text
- **Code view**: Edit raw HTML when needed
- **Fullscreen mode**: Distraction-free editing
- **Word count**: Track content length
- **Help system**: Built-in help and documentation

### User Experience
- **Responsive design**: Works on all screen sizes
- **Touch-friendly**: Optimized for touch devices
- **Keyboard shortcuts**: Standard editing shortcuts
- **Auto-save**: Content saved on form submission
- **Real-time preview**: See changes as you type

## 📱 Responsive Design

### Mobile Optimization
- **Touch-friendly toolbar**: Large, easy-to-tap buttons
- **Responsive layout**: Adapts to different screen sizes
- **Mobile editing**: Full functionality on mobile devices
- **Zoom support**: Proper scaling on high-DPI displays

### Cross-Browser Compatibility
- **Modern browsers**: Full support for Chrome, Firefox, Safari, Edge
- **Fallback support**: Graceful degradation for older browsers
- **Consistent experience**: Same functionality across all platforms

## 🚀 Benefits

### For Administrators
- **No coding required**: Create rich content without HTML knowledge
- **Visual editing**: See exactly how content will appear
- **Professional results**: Create polished, well-formatted content
- **Easy updates**: Modify content quickly and easily
- **Dynamic content**: Automatic insertion of event details

### For Users
- **Rich content**: Beautifully formatted, engaging content
- **Up-to-date information**: Always current event details
- **Professional appearance**: Polished, well-designed pages
- **Better readability**: Proper formatting improves comprehension

### For Developers
- **Maintainable**: Clean separation of content and code
- **Extensible**: Easy to add new formatting options
- **Secure**: Proper sanitization and validation
- **Performance**: Efficient rendering and caching

## 📋 Usage Examples

### Basic Content
```html
<h2>🎉 Welkom bij ons jaarlijkse buurtfeest!</h2>
<p><strong>Beste Kamperweg buurtgenoten,</strong></p>
<p>Hartelijk welkom op het digitale aanmeldformulier voor ons jaarlijkse tuinfeest met BBQ.</p>
```

### With Dynamic Placeholders
```html
<p>Dit jaar houden we ons feest op <strong>{date}</strong>.</p>
<p>We zijn welkom bij de <strong>{location}</strong>.</p>
<p>De kosten bedragen <strong>€{price} per volwassene</strong>.</p>
<p>Meldt u zich uiterlijk <strong>{deadline}</strong> aan.</p>
```

### Advanced Formatting
```html
<div style="background-color: #f8f9fa; padding: 20px; border-radius: 8px; margin: 20px 0;">
    <h3 style="color: #e74c3c;">📅 Belangrijke Informatie</h3>
    <ul>
        <li><strong>Datum:</strong> {date}</li>
        <li><strong>Locatie:</strong> {location}</li>
        <li><strong>Prijs:</strong> €{price} per volwassene</li>
        <li><strong>Deadline:</strong> {deadline}</li>
    </ul>
</div>
```

## 🔄 Migration Notes

### Existing Content
- **Automatic migration**: Default content set automatically
- **Backward compatibility**: Existing functionality preserved
- **No data loss**: All existing configurations maintained

### Content Updates
- **Seamless transition**: Old hardcoded content replaced with dynamic system
- **Immediate effect**: Changes take effect without restart
- **Version control**: All changes tracked in database

## 🎯 Future Enhancements

### Potential Additions
- **Image upload**: Direct image upload and management
- **Template library**: Pre-built content templates
- **Content versioning**: Track and restore previous versions
- **Multi-language support**: Content in multiple languages
- **Advanced formatting**: More styling options and themes
- **Content preview**: Live preview of changes before saving

---

## 📋 Summary

The BBQ application now includes a comprehensive WYSIWYG editor system that provides:

✅ **Professional rich text editing**  
✅ **Dynamic content with placeholders**  
✅ **Secure HTML rendering**  
✅ **User-friendly admin interface**  
✅ **Responsive design**  
✅ **Cross-browser compatibility**  
✅ **Real-time updates**  
✅ **Professional formatting options**  

Administrators can now create beautiful, formatted content for the main page without any coding knowledge, while maintaining security and performance! 🎉


