
'''
This module contains the Visualizer class for the audio monitor GUI.
'''
import tkinter as tk
from .constants import PADDING, NUM_BANDS, SOUND_THRESHOLD, WINDOW_WIDTH, WINDOW_HEIGHT
from .logger_config import logger

class Visualizer:
    '''Handles the drawing of all elements on the canvas.'''

    def __init__(self, root, colors, fonts, num_bands: int, band_labels: list):
        self.root = root
        self.colors = colors
        self.fonts = fonts
        self.num_bands = num_bands # Store the actual number of bands
        self.band_labels = band_labels # Store the band labels
        self.canvas = None
        self.bars = []
        self.labels = []
        self.grid_lines = []
        self.grid_labels = []
        self.BUTTON_FRAME_HEIGHT = 50
        
        self.TOP_MARGIN = 40
        self.BOTTOM_MARGIN = 30
        self.FREQ_LABEL_HEIGHT = 20
        
        self.bar_area_top = self.TOP_MARGIN
        # Initial calculations will be done in create_canvas and on_window_resize
        self.bar_area_bottom = 0 # Will be set dynamically
        self.bar_area_height = 0 # Will be set dynamically
        
        self.viz_dimensions = {
            'top': self.TOP_MARGIN,
            'bottom': 0,
            'height': 0,
            'bar_width': 0,
            'gap': 0
        }
        logger.debug("Visualizer initialized.")


    def create_canvas(self, parent, width, height, button_height):
        '''Create the main canvas.'''
        logger.debug(f"Creating canvas with width={width}, height={height - button_height}")
        self.canvas = tk.Canvas(
            parent,
            width=width,
            height=height - button_height,
            highlightthickness=0,
            bg=self.colors['bg']
        )
        self.canvas.pack(fill=tk.BOTH, expand=True)
        self.canvas_width = width
        self.canvas_height = height - button_height # This is the height of the canvas itself
        self._create_gradient_background(self.canvas_width, self.canvas_height)
        logger.debug("Canvas created and gradient background applied.")
        return self.canvas

    def setup_frequency_bars(self):
        '''Set up the frequency visualization bars.'''
        logger.debug("Setting up frequency bars.")
        logger.debug(f"setup_frequency_bars: bar_area_top={self.bar_area_top}, bar_area_bottom={self.bar_area_bottom}, bar_area_height={self.bar_area_height}")
        usable_width = self.canvas_width - (2 * PADDING)
        bar_width = (usable_width) // self.num_bands
        gap = 2
        self.viz_dimensions = {
            'top': self.bar_area_top,
            'bottom': self.bar_area_bottom,
            'height': self.bar_area_height,
            'bar_width': bar_width,
            'gap': gap
        }
        self.bars = []
        self.labels = []
        for i in range(self.num_bands):
            x0 = PADDING + (i * (bar_width + gap))
            x1 = x0 + bar_width
            bar = self.canvas.create_rectangle(
                x0, self.bar_area_bottom,
                x1, self.bar_area_bottom,
                fill=self.colors['bar_colors']['low'],
                outline='#555555',
                tags='bars'
            )
            self.bars.append(bar)
            freq_text = self.band_labels[i]
            label_y = self.bar_area_bottom + (self.FREQ_LABEL_HEIGHT // 2)
            label = self.canvas.create_text(
                (x0 + x1) // 2,
                label_y,
                text=freq_text,
                fill=self.colors['text'],
                font=('Arial', 10),
                anchor='n',
                tags='frequency_labels'
            )
            self.labels.append(label)
        logger.debug(f"Created {len(self.bars)} frequency bars and labels.")

    def setup_grid(self):
        '''Set up the visualization grid.'''
        logger.debug("Setting up visualization grid.")
        logger.debug(f"setup_grid: bar_area_top={self.bar_area_top}, bar_area_bottom={self.bar_area_bottom}, bar_area_height={self.bar_area_height}")
        self.canvas.create_text(
            WINDOW_WIDTH // 2,
            PADDING // 2 + 10,
            text='Bar Height: Output Level (% / dBFS)',
            fill='white',
            font=('Arial', 16, 'bold'),
            tags="header"
        )
        self.create_grid_lines()
        logger.debug("Grid setup complete.")

    def create_grid_lines(self):
        '''Create grid lines and labels.'''
        logger.debug("Creating grid lines and labels.")
        self.grid_lines = []
        self.grid_labels = []
        percentages = [100, 80, 60, 40, 20, 0]
        for i, percentage in enumerate(percentages):
            frac = i / (len(percentages) - 1)
            y = self.bar_area_top + int(frac * self.bar_area_height)
            line = self.canvas.create_line(
                PADDING, y,
                WINDOW_WIDTH - PADDING, y,
                fill=self.colors['grid'],
                dash=(2, 4),
                width=1,
                stipple='gray50',
                tags='grid'
            )
            self.grid_lines.append(line)
            label = self.canvas.create_text(
                PADDING - 5, y,
                text=f"{percentage}%",
                fill=self.colors['text'],
                font=self.fonts['small'],
                anchor='e',
                tags='labels'
            )
            self.grid_labels.append(label)
        logger.debug(f"Created {len(self.grid_lines)} grid lines and {len(self.grid_labels)} grid labels.")

    def update_frequency_bars(self, band_values):
        '''Update the frequency visualization bars with modern effects.'''
        if not hasattr(self, 'viz_dimensions') or not self.viz_dimensions:
            logger.warning("Viz dimensions not set, cannot update frequency bars.")
            return
        viz_top = self.viz_dimensions['top']
        viz_bottom = self.viz_dimensions['bottom']
        viz_height = self.viz_dimensions['height']
        bar_width = self.viz_dimensions['bar_width']
        gap = self.viz_dimensions['gap']
        for i, value in enumerate(band_values[:self.num_bands]):
            if i >= len(self.bars):
                logger.debug(f"Skipping bar update for index {i}, beyond existing bars count.")
                continue
            height_percent = value * 100
            if hasattr(self, 'last_heights') and i in self.last_heights:
                if height_percent > self.last_heights[i]:
                    height_percent = 0.1 * self.last_heights[i] + 0.9 * height_percent
                else:
                    height_percent = 0.1 * self.last_heights[i] + 0.9 * height_percent
            if not hasattr(self, 'last_heights'):
                self.last_heights = {}
            self.last_heights[i] = height_percent
            x0 = PADDING + (i * (bar_width + gap))
            x1 = x0 + bar_width
            height = int((height_percent / 100.0) * viz_height)
            y0 = viz_bottom - height
            y1 = viz_bottom
            self.canvas.coords(self.bars[i], x0, y0, x1, y1)
            logger.debug(f"Bar {i} updated: value={value:.2f}, height_percent={height_percent:.2f}%, coords=({x0}, {y0}, {x1}, {y1})")
            if value <= SOUND_THRESHOLD:
                color = self.colors['bg']
            elif height_percent <= 40:
                color = self.colors['bar_colors']['low']
            elif height_percent <= 60:
                color = self.colors['bar_colors']['mid']
            elif height_percent <= 80:
                color = self.colors['bar_colors']['high']
            else:
                color = self.colors['bar_colors']['peak']
            self.canvas.itemconfig(
                self.bars[i],
                fill=color,
                outline='#555555' # Keep a consistent border color
            )
            logger.debug(f"Bar {i} color updated to {color}.")
        logger.debug("Frequency bars updated.")

    def on_window_resize(self, event, window_state, button_frame, band_values):
        '''Handle window resize events.'''
        logger.debug(f"Handling window resize event. Minimized: {window_state['minimized']}")
        if event and event.widget == self.root and not window_state['minimized']:
            window_state['width'] = event.width
            window_state['height'] = event.height
            total_height = event.height
            total_width = event.width
            available_height = total_height - self.BUTTON_FRAME_HEIGHT
            
            self.bar_area_top = self.TOP_MARGIN
            self.bar_area_height = (
                available_height - self.TOP_MARGIN - self.BOTTOM_MARGIN - self.FREQ_LABEL_HEIGHT
            )
            self.bar_area_bottom = self.bar_area_top + self.bar_area_height
            self.viz_dimensions['top'] = self.bar_area_top
            self.viz_dimensions['bottom'] = self.bar_area_bottom
            self.viz_dimensions['height'] = self.bar_area_height

            logger.debug(f"on_window_resize: bar_area_top={self.bar_area_top}, bar_area_bottom={self.bar_area_bottom}, bar_area_height={self.bar_area_height}")

            self.canvas.place(x=0, y=0, width=total_width, height=available_height)
            button_frame.place(x=0, y=available_height, width=total_width, height=self.BUTTON_FRAME_HEIGHT)

            # Update canvas_width and canvas_height for internal calculations
            self.canvas_width = total_width
            self.canvas_height = available_height

            # Recalculate bar area dimensions based on new canvas_height
            self.bar_area_top = self.TOP_MARGIN
            self.bar_area_bottom = self.canvas_height - self.BOTTOM_MARGIN - self.FREQ_LABEL_HEIGHT
            self.bar_area_height = self.bar_area_bottom - self.bar_area_top
            logger.debug(f"Recalculated bar area: top={self.bar_area_top}, bottom={self.bar_area_bottom}, height={self.bar_area_height}")

            for widget in self.grid_lines + self.grid_labels:
                self.canvas.delete(widget)
            self.canvas.delete("gradient")
            self.create_grid_lines()
            self._create_gradient_background(total_width, total_height)
            header_items = self.canvas.find_withtag("header")
            header_font_size = max(12, min(24, int(total_width / 50)))
            for item in header_items:
                self.canvas.coords(item, total_width // 2, self.TOP_MARGIN // 2)
                self.canvas.itemconfig(item, font=('Arial', header_font_size, 'bold'))
            
            usable_width = total_width - (2 * PADDING)
            bar_width = max(4, (usable_width // self.num_bands) - 2)
            spacing = (usable_width - (bar_width * self.num_bands)) // (self.num_bands + 1)
            logger.debug(f"Bar dimensions: bar_width={bar_width}, spacing={spacing}")

            self.viz_dimensions['bar_width'] = bar_width
            self.viz_dimensions['gap'] = spacing
            
            for i in range(self.num_bands):
                x0 = PADDING + spacing + i * (bar_width + spacing)
                x1 = x0 + bar_width
                if i < len(self.bars):
                    self.canvas.coords(
                        self.bars[i],
                        x0, self.bar_area_bottom,
                        x1, self.bar_area_bottom
                    )
                if i < len(self.labels):
                    font_size = max(6, min(10, int(bar_width / 2.5)))
                    logger.debug(f"Band {i} label font size: {font_size}")
                    # Dynamically adjust label height based on font size
                    current_freq_label_height = font_size + 4 # Add some padding
                    y_label = self.bar_area_bottom + (current_freq_label_height // 2)
                    self.canvas.coords(
                        self.labels[i],
                        (x0 + x1) // 2,
                        y_label
                    )
                    self.canvas.itemconfig(
                        self.labels[i],
                        text=self.band_labels[i],
                        font=('Arial', font_size)
                    )
            self.update_frequency_bars(band_values)
            logger.debug(f"Window resized to {total_width}x{total_height}. Visualizer elements updated.")

    def _create_gradient_background(self, width, height):
        '''Create gradient background.'''
        logger.debug(f"Creating gradient background for {width}x{height}.")
        for i in range(height):
            factor = i / height
            r = int(30 + (factor * 10))
            g = int(30 + (factor * 10))
            b = int(30 + (factor * 10))
            color = f'#{r:02x}{g:02x}{b:02x}'
            self.canvas.create_line(0, i, width, i, fill=color, tags=("gradient", "background"))
        self.canvas.tag_lower('background')
        logger.debug("Gradient background created.")

    def update_layering(self):
        '''Update the layering of canvas elements.'''
        self.canvas.tag_raise('bars', 'background')
        self.canvas.tag_raise('grid', 'bars')
        self.canvas.tag_raise('labels', 'grid')
        logger.debug("Canvas layering updated.")
