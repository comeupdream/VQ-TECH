"""Theme manager for applying color schemes to pyobd UI."""
import wx
from themes import get_theme, get_all_themes, DEFAULT_THEME


class ThemeManager:
    """Manages theme application to wxPython UI elements."""

    def __init__(self, current_theme=DEFAULT_THEME):
        self.current_theme_name = current_theme
        self.current_theme = get_theme(current_theme)

    def set_theme(self, theme_name):
        """Switch to a different theme."""
        if theme_name not in get_all_themes():
            return False
        self.current_theme_name = theme_name
        self.current_theme = get_theme(theme_name)
        return True

    def apply_to_window(self, window):
        """Apply theme to a wx.Window and its children."""
        theme = self.current_theme

        # Apply to main window
        if isinstance(window, wx.Frame) or isinstance(window, wx.Dialog):
            window.SetBackgroundColour(self._rgb_to_wx(theme['primary_bg']))

        # Recursively apply to all children
        self._apply_to_children(window, theme)

    def _apply_to_children(self, parent, theme):
        """Recursively apply theme to child widgets."""
        for child in parent.GetChildren():
            self._apply_to_widget(child, theme)
            # Recurse into containers
            if hasattr(child, 'GetChildren'):
                self._apply_to_children(child, theme)

    def _apply_to_widget(self, widget, theme):
        """Apply theme colors to a specific widget."""
        try:
            if isinstance(widget, wx.StaticText):
                widget.SetForegroundColour(self._rgb_to_wx(theme['primary_text']))
                widget.SetBackgroundColour(self._rgb_to_wx(theme['primary_bg']))

            elif isinstance(widget, wx.TextCtrl):
                widget.SetForegroundColour(self._rgb_to_wx(theme['primary_text']))
                widget.SetBackgroundColour(self._rgb_to_wx(theme['secondary_bg']))

            elif isinstance(widget, wx.Choice) or isinstance(widget, wx.ComboBox):
                widget.SetForegroundColour(self._rgb_to_wx(theme['primary_text']))
                widget.SetBackgroundColour(self._rgb_to_wx(theme['secondary_bg']))

            elif isinstance(widget, wx.Button):
                widget.SetForegroundColour(self._rgb_to_wx(theme['primary_text']))
                widget.SetBackgroundColour(self._rgb_to_wx(theme['secondary_bg']))

            elif isinstance(widget, wx.Panel):
                widget.SetBackgroundColour(self._rgb_to_wx(theme['primary_bg']))

            elif isinstance(widget, wx.ListCtrl) or isinstance(widget, wx.ListBox):
                widget.SetForegroundColour(self._rgb_to_wx(theme['primary_text']))
                widget.SetBackgroundColour(self._rgb_to_wx(theme['secondary_bg']))

            elif isinstance(widget, wx.Gauge):
                # Gauge styling is limited in wxPython, but we can set colors
                pass

            elif isinstance(widget, wx.Grid):
                widget.SetDefaultCellTextColour(self._rgb_to_wx(theme['primary_text']))
                widget.SetDefaultCellBackgroundColour(self._rgb_to_wx(theme['secondary_bg']))
                widget.SetLabelTextColour(self._rgb_to_wx(theme['primary_text']))
                widget.SetLabelBackgroundColour(self._rgb_to_wx(theme['secondary_bg']))

        except (AttributeError, wx.wxAssertionError):
            # Some widgets don't support color changes, skip them
            pass

    @staticmethod
    def _rgb_to_wx(rgb_tuple):
        """Convert (R, G, B) tuple to wx.Colour."""
        return wx.Colour(*rgb_tuple)

    def get_color(self, key):
        """Get a specific color from current theme."""
        return self._rgb_to_wx(self.current_theme.get(key, self.current_theme['primary_text']))

    def get_theme_name(self):
        """Get current theme name."""
        return self.current_theme_name

    def get_all_theme_names(self):
        """Get list of all available theme names."""
        return get_all_themes()
