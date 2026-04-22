"""Dark cyber/game theme for Dear PyGui."""
import dearpygui.dearpygui as dpg

BG        = (12, 15, 20)
PANEL     = (20, 26, 34)
ACCENT    = (0, 255, 200)
ACCENT_2  = (255, 60, 120)
WARN      = (255, 180, 0)
DANGER    = (255, 60, 60)
TEXT      = (230, 240, 245)
MUTED     = (120, 140, 150)
GRID      = (35, 45, 55)


def apply_global_theme():
    with dpg.theme() as theme:
        with dpg.theme_component(dpg.mvAll):
            dpg.add_theme_color(dpg.mvThemeCol_WindowBg, BG)
            dpg.add_theme_color(dpg.mvThemeCol_ChildBg, PANEL)
            dpg.add_theme_color(dpg.mvThemeCol_FrameBg, PANEL)
            dpg.add_theme_color(dpg.mvThemeCol_Text, TEXT)
            dpg.add_theme_color(dpg.mvThemeCol_Border, ACCENT)
            dpg.add_theme_color(dpg.mvThemeCol_Button, (30, 40, 50))
            dpg.add_theme_color(dpg.mvThemeCol_ButtonHovered, ACCENT)
            dpg.add_theme_color(dpg.mvThemeCol_ButtonActive, ACCENT_2)
            dpg.add_theme_color(dpg.mvThemeCol_TitleBg, PANEL)
            dpg.add_theme_color(dpg.mvThemeCol_TitleBgActive, (30, 40, 50))
            dpg.add_theme_style(dpg.mvStyleVar_FrameRounding, 6)
            dpg.add_theme_style(dpg.mvStyleVar_WindowRounding, 8)
            dpg.add_theme_style(dpg.mvStyleVar_FrameBorderSize, 1)
            dpg.add_theme_style(dpg.mvStyleVar_WindowPadding, 10, 10)
    dpg.bind_theme(theme)


def plot_theme():
    with dpg.theme() as t:
        with dpg.theme_component(dpg.mvLineSeries):
            dpg.add_theme_color(dpg.mvPlotCol_Line, ACCENT, category=dpg.mvThemeCat_Plots)
            dpg.add_theme_style(dpg.mvPlotStyleVar_LineWeight, 2, category=dpg.mvThemeCat_Plots)
    return t
