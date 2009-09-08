function(html) {
  html = html.replace(/<\s*p[^>]*>/gi, '');
  html = html.replace(/<\/\s*p\s*>/gi, '');
  html = html.trim();
  return html;
} 