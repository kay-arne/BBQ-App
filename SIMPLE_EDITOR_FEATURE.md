# ✏️ Simple Content Editor

## Overview
The BBQ application now includes a lightweight, custom content editor that provides basic formatting options and easy access to dynamic variables - **no external APIs required!**

## 🎯 Features

### **Simple Formatting**
- ✅ **Bold text** - Select text and click **B** or use Ctrl+B
- ✅ **Italic text** - Select text and click **I** or use Ctrl+I  
- ✅ **Underlined text** - Select text and click **U** or use Ctrl+U

### **Dynamic Variables**
- ✅ **📅 Datum** - Inserts `{date}` (BBQ event date)
- ✅ **📍 Locatie** - Inserts `{location}` (Event location)
- ✅ **💰 Prijs** - Inserts `{price}` (Price per adult)
- ✅ **⏰ Deadline** - Inserts `{deadline}` (Registration deadline)

### **User Experience**
- ✅ **No external dependencies** - Works offline, no API calls
- ✅ **Keyboard shortcuts** - Standard Ctrl+B, Ctrl+I, Ctrl+U
- ✅ **Click to insert** - Easy variable insertion with one click
- ✅ **Monospace font** - Easy to read and edit HTML
- ✅ **Professional styling** - Matches the admin interface

## 🛠️ How It Works

### **For Administrators**

1. **Access the Editor**:
   - Login to admin panel
   - Navigate to "⚙️ Configuratie"
   - Find "📝 Inhoud" section
   - Locate "Hoofdinhoud van de aanmeldpagina (HTML)"

2. **Format Text**:
   - Select text in the textarea
   - Click **B** for bold, **I** for italic, **U** for underline
   - Or use keyboard shortcuts: Ctrl+B, Ctrl+I, Ctrl+U

3. **Insert Variables**:
   - Click any variable button (📅 Datum, 📍 Locatie, etc.)
   - Variables are inserted at cursor position
   - They will be automatically replaced with actual values

4. **Save Changes**:
   - Click "💾 Configuratie Opslaan"
   - Changes take effect immediately

### **Example Usage**

```html
<h2>🎉 Welkom bij ons jaarlijkse buurtfeest!</h2>

<p><strong>Beste Kamperweg buurtgenoten,</strong></p>

<p>Hartelijk welkom op het digitale aanmeldformulier voor ons jaarlijkse tuinfeest met BBQ. Dit jaar houden we ons feest op <strong>{date}</strong>. We zijn voor ons feest welkom bij de <strong>{location}</strong>.</p>

<p>De kosten voor de BBQ bedragen <strong>€{price} per volwassene</strong>. Alles is inbegrepen: een complete BBQ, op- en afbouw tuinfeest, schoonmaak BBQ's, koffie, thee en overige (non) alcoholische dranken.</p>

<p>Meldt u zich alstublieft <strong>uiterlijk {deadline}</strong> aan via dit formulier.</p>
```

## 🎨 Editor Interface

### **Toolbar Layout**
```
[B] [I] [U] | [📅 Datum] [📍 Locatie] [💰 Prijs] [⏰ Deadline]
```

### **Button Functions**
- **B** - Bold formatting (`<strong>`)
- **I** - Italic formatting (`<em>`)
- **U** - Underline formatting (`<u>`)
- **📅 Datum** - Insert `{date}` placeholder
- **📍 Locatie** - Insert `{location}` placeholder
- **💰 Prijs** - Insert `{price}` placeholder
- **⏰ Deadline** - Insert `{deadline}` placeholder

## 🔧 Technical Implementation

### **No External Dependencies**
- ❌ No TinyMCE API calls
- ❌ No external CDN dependencies
- ❌ No complex JavaScript libraries
- ✅ Pure HTML, CSS, and vanilla JavaScript

### **Simple JavaScript Functions**
```javascript
function formatText(command) {
    // Selects text and wraps with HTML tags
    // Supports: bold, italic, underline
}

function insertVariable(variable) {
    // Inserts variable at cursor position
    // Supports: {date}, {location}, {price}, {deadline}
}
```

### **Keyboard Shortcuts**
- **Ctrl+B** (or Cmd+B on Mac) - Bold
- **Ctrl+I** (or Cmd+I on Mac) - Italic  
- **Ctrl+U** (or Cmd+U on Mac) - Underline

### **CSS Styling**
- Professional toolbar with hover effects
- Monospace font for easy HTML editing
- Responsive design for all screen sizes
- Consistent with admin interface theme

## 🚀 Benefits

### **Performance**
- ✅ **Fast loading** - No external API calls
- ✅ **Offline capable** - Works without internet
- ✅ **Lightweight** - Minimal JavaScript overhead
- ✅ **No dependencies** - Self-contained solution

### **User Experience**
- ✅ **Simple to use** - Intuitive interface
- ✅ **Quick formatting** - One-click text styling
- ✅ **Easy variables** - Click to insert placeholders
- ✅ **Keyboard shortcuts** - Standard editing shortcuts

### **Maintenance**
- ✅ **No API keys** - No external service dependencies
- ✅ **No updates needed** - Self-contained solution
- ✅ **Easy to modify** - Simple JavaScript functions
- ✅ **Reliable** - No external service failures

## 📱 Responsive Design

### **Mobile Friendly**
- ✅ **Touch-friendly buttons** - Large, easy-to-tap buttons
- ✅ **Responsive toolbar** - Wraps on smaller screens
- ✅ **Mobile editing** - Full functionality on mobile devices
- ✅ **Zoom support** - Proper scaling on all devices

### **Cross-Browser**
- ✅ **Modern browsers** - Chrome, Firefox, Safari, Edge
- ✅ **Consistent experience** - Same functionality everywhere
- ✅ **No polyfills needed** - Uses standard web APIs

## 🔒 Security

### **Safe HTML Output**
- ✅ **Server-side rendering** - HTML processed safely
- ✅ **Flask Markup** - Secure HTML output
- ✅ **No XSS risks** - Proper content sanitization
- ✅ **CSRF protection** - All forms protected

## 📋 Usage Examples

### **Basic Formatting**
```html
<p>This is <strong>bold text</strong> and <em>italic text</em> and <u>underlined text</u>.</p>
```

### **With Variables**
```html
<p>Our BBQ will be on <strong>{date}</strong> at <strong>{location}</strong>.</p>
<p>The cost is <strong>€{price} per adult</strong>.</p>
<p>Please register by <strong>{deadline}</strong>.</p>
```

### **Complex Layout**
```html
<h2>🎉 Welcome to our BBQ!</h2>

<div style="background: #f8f9fa; padding: 20px; border-radius: 8px;">
    <h3>📅 Event Details</h3>
    <ul>
        <li><strong>Date:</strong> {date}</li>
        <li><strong>Location:</strong> {location}</li>
        <li><strong>Price:</strong> €{price} per adult</li>
        <li><strong>Deadline:</strong> {deadline}</li>
    </ul>
</div>
```

## 🎯 Perfect For

### **This Use Case**
- ✅ **Simple content editing** - Basic formatting is sufficient
- ✅ **Dynamic variables** - Easy access to BBQ details
- ✅ **No complexity** - Users don't need advanced features
- ✅ **Reliability** - No external dependencies to fail

### **When to Use**
- ✅ **Simple websites** - Basic content management
- ✅ **Event pages** - Dynamic information display
- ✅ **Admin interfaces** - Quick content updates
- ✅ **Offline environments** - No internet required

## 🔄 Migration from TinyMCE

### **What Changed**
- ❌ **Removed**: TinyMCE external API dependency
- ❌ **Removed**: Complex WYSIWYG features
- ✅ **Added**: Simple formatting buttons
- ✅ **Added**: Variable insertion buttons
- ✅ **Added**: Keyboard shortcuts
- ✅ **Added**: Professional styling

### **Benefits of Change**
- ✅ **Faster loading** - No external API calls
- ✅ **More reliable** - No external service dependencies
- ✅ **Simpler interface** - Easier for users to understand
- ✅ **Better performance** - Lighter JavaScript footprint

---

## 📋 Summary

The BBQ application now features a **lightweight, custom content editor** that provides:

✅ **Simple formatting** (bold, italic, underline)  
✅ **Dynamic variables** (date, location, price, deadline)  
✅ **No external APIs** - Completely self-contained  
✅ **Keyboard shortcuts** - Standard editing shortcuts  
✅ **Professional styling** - Matches admin interface  
✅ **Mobile-friendly** - Works on all devices  
✅ **Fast and reliable** - No external dependencies  

**Perfect for simple content editing with dynamic variables - exactly what you need!** 🎉

