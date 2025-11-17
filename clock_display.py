# clock_display.py

import pygame
import datetime
import pytz
import os

class ClockDisplay:
    """
    Handles the drawing of the top status bar, drop shadow, and the real-time clock.
    """
    
    # Configuration
    BAR_COLOR = (23, 29, 34)
    SHADOW_COLOR = (0, 0, 0) # Black
    TEXT_COLOR = (255, 255, 255) # White
    SHADOW_OFFSET = 3
    PADDING = 10
    
    def __init__(self, screen, screen_width, screen_height, font_path, time_zone_str, bar_height):
        self.screen = screen
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.time_zone = pytz.timezone(time_zone_str)
        self.bar_height = bar_height
        
        # Define the rectangle for the top bar
        self.bar_rect = pygame.Rect(0, 0, self.screen_width, self.bar_height)
        
        # Load the font. Use a smaller size for the clock compared to the main display.
        # Fallback to default if the provided path is not found.
        font_size = round(bar_height * .75)
        try:
            self.font = pygame.font.Font(font_path, font_size)
        except (FileNotFoundError, IOError):
            print(f"Warning: Custom font not found at {font_path}. Using default system font.")
            self.font = pygame.font.Font(None, font_size)

    def draw_top_bar(self):
        """Draws the dark bar with a drop shadow effect."""
        
        # 1. Draw the Drop Shadow (offset down and right)
        shadow_rect = self.bar_rect.copy()
        shadow_rect.x += self.SHADOW_OFFSET
        shadow_rect.y += self.SHADOW_OFFSET
        
        # Draw the shadow (only the bottom and right edges will show)
        pygame.draw.rect(self.screen, self.SHADOW_COLOR, shadow_rect)
        
        # 2. Draw the Main Bar (covers the rest of the shadow)
        pygame.draw.rect(self.screen, self.BAR_COLOR, self.bar_rect)

    def draw_clock(self):
        """Renders and draws the current time in the top right corner."""
        
        # Get the current time in the specified time zone
        current_dt = datetime.datetime.now(self.time_zone)
        # Format: HH:MM AM/PM (e.g., 10:49 PM)
        time_str = current_dt.strftime("%I:%M %p")
        
        # Render the text surface
        text_surface = self.font.render(time_str, True, self.TEXT_COLOR)
        
        # Calculate the position
        text_rect = text_surface.get_rect()
        
        # Position: Right side of the screen, centered vertically in the bar, with padding
        text_rect.right = self.screen_width - self.PADDING
        text_rect.centery = self.bar_height // 2 
        
        # Draw the clock
        self.screen.blit(text_surface, text_rect)
        
    def draw(self):
        """Combined method to draw the entire status bar."""
        self.draw_top_bar()
        self.draw_clock()