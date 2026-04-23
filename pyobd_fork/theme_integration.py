"""Integration helper to add theming to pyobd.py

This module provides functions to integrate the theme system into the existing pyobd UI.
"""
import wx
from theme_manager import ThemeManager
from themes import get_theme


def setup_theme_menu(app_instance, menu_bar):
    """Add a Theme menu to the menu bar."""
    theme_menu = wx.Menu()

    theme_manager = app_instance.theme_manager
    theme_names = theme_manager.get_all_theme_names()

    for idx, theme_name in enumerate(theme_names):
        menu_id = wx.NewIdRef()
        display_name = get_theme(theme_name)['name']
        item = theme_menu.Append(menu_id, display_name, kind=wx.ITEM_RADIO)

        # Check the current theme
        if theme_name == theme_manager.get_theme_name():
            item.Check(True)

        # Bind event handler
        app_instance.Bind(wx.EVT_MENU,
                         lambda evt, tn=theme_name: app_instance.OnThemeChange(tn),
                         item)

    menu_bar.Append(theme_menu, "&Theme")
    return theme_menu


def apply_theme_to_frame(frame, theme_manager):
    """Apply current theme to the entire frame."""
    theme_manager.apply_to_window(frame)
    frame.Refresh()


def setup_theme_manager(app_instance, theme_name='tron'):
    """Initialize theme manager on app instance."""
    app_instance.theme_manager = ThemeManager(theme_name)
    return app_instance.theme_manager


def create_theme_button_panel(parent, app_instance):
    """Create a panel with theme selection buttons."""
    panel = wx.Panel(parent, -1)
    sizer = wx.BoxSizer(wx.HORIZONTAL)

    label = wx.StaticText(panel, -1, "Theme:")
    sizer.Add(label, 0, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 5)

    theme_manager = app_instance.theme_manager
    theme_names = theme_manager.get_all_theme_names()

    for theme_name in theme_names:
        display_name = get_theme(theme_name)['name'].split()[0]
        btn = wx.Button(panel, -1, display_name)
        btn.Bind(wx.EVT_BUTTON,
                lambda evt, tn=theme_name: app_instance.OnThemeChange(tn))
        sizer.Add(btn, 0, wx.ALL, 5)

    panel.SetSizer(sizer)
    return panel
