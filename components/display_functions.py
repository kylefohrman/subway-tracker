def wrap_text(text, font, max_width):
    """Wraps text to fit within a maximum pixel width."""
    lines = []
    words = text.split(' ')
    current_line = []
    for word in words:
        # Check the width if the new word is added
        if font.size(' '.join(current_line + [word]))[0] <= max_width:
            current_line.append(word)
        else:
            # Start a new line
            lines.append(' '.join(current_line))
            current_line = [word]
    lines.append(' '.join(current_line)) # Add the last line
    return lines

# This handles the "minutes until" section for each arrival row
# We want each number to have its own color, depending on its arrival status
def draw_multi_colored_text(surface, data, surface_width, start_y, right_offset, font):
    # --- STEP 1: Calculate the Total Width ---
    total_width = 0
    
    # We create a list of rendered surfaces and calculate the total width
    rendered_parts = []
    
    for text_part, color in data:
        # Render the text part (we need to do this to get the exact width)
        text_surface = font.render(text_part, True, color)
        
        # Store the surface and its width
        rendered_parts.append((text_surface, text_surface.get_width()))
        
        # Accumulate the width
        total_width += text_surface.get_width()
        
    # --- STEP 2: Determine the Starting X-Coordinate ---
    # The starting X is the screen's right edge, minus the total text width, 
    # minus the desired offset.
    start_x = surface_width - total_width - right_offset
    
    # --- STEP 3: Draw the Text ---
    x_offset = start_x
    
    for text_surface, width in rendered_parts:
        # Blit (draw) the surface onto the screen
        surface.blit(text_surface, (x_offset, start_y))
        
        # Increment the x_offset by the width of the text we just drew
        x_offset += width