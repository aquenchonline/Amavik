import streamlit.components.v1 as components  # <--- Make sure this is imported

def inject_enter_key_navigation():
    # This JavaScript code listens for the "Enter" key and simulates a "Tab" key press
    js_code = """
    <script>
    document.addEventListener('DOMContentLoaded', function() {
        const doc = window.parent.document;
        
        // Find all input fields (text, number, date, etc.)
        const inputs = doc.querySelectorAll('input, textarea, select');
        
        inputs.forEach((input, index) => {
            input.addEventListener('keydown', function(e) {
                // If Enter is pressed (and Shift is NOT pressed - to allow Shift+Enter in textareas)
                if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault(); // Stop the form from submitting
                    
                    // Find the next input
                    const nextInput = inputs[index + 1];
                    
                    if (nextInput) {
                        nextInput.focus(); // Move focus
                        nextInput.select(); // Highlight the text in the next box (optional)
                    }
                }
            });
        });
    });
    </script>
    """
    # Inject into the app
    components.html(js_code, height=0, width=0)
