# Custom Jinja filter to render markdown as HTML
def markdown_filter(text):
    if not text:
        return ""
    try:
        return Markup(markdown.markdown(text))
    except Exception as e:
        print(f"Error rendering markdown: {e}")
        return Markup(f"<p>Error rendering markdown: {e}</p><pre>{text}</pre>") 