"""
Non-blocking WPF toast notifications.

Toasts run on a dedicated STA UI thread with its own Dispatcher, so they never
block the Revit UI thread and never need to wait for Revit to be idle.
"""
import threading

import clr
clr.AddReference("PresentationFramework")
clr.AddReference("PresentationCore")
clr.AddReference("WindowsBase")

from System import Action, TimeSpan
from System.Threading import Thread, ThreadStart, ApartmentState
from System.Windows import (
    Window, WindowStyle, ResizeMode, WindowStartupLocation,
    Thickness, SystemParameters, CornerRadius, FontWeights, FontStyles,
    SizeToContent, TextWrapping,
)
from System.Windows.Controls import StackPanel, TextBlock, Border, Orientation
from System.Windows.Media import Brushes, SolidColorBrush, ColorConverter
from System.Windows.Threading import Dispatcher, DispatcherTimer

from revitsync.config import TOAST_LIFETIME_S


_TOAST_WIDTH = 380
_TOAST_GAP = 12
_SCREEN_MARGIN = 16

_dispatcher = None
_dispatcher_ready = threading.Event()
_dispatcher_lock = threading.Lock()
_active_toasts = []  # most-recent first


def _ui_thread_main():
    global _dispatcher
    _dispatcher = Dispatcher.CurrentDispatcher
    _dispatcher_ready.set()
    Dispatcher.Run()


def _ensure_dispatcher():
    global _dispatcher
    if _dispatcher is not None:
        return
    with _dispatcher_lock:
        if _dispatcher is not None:
            return
        t = Thread(ThreadStart(_ui_thread_main))
        t.SetApartmentState(ApartmentState.STA)
        t.IsBackground = True
        t.Start()
        _dispatcher_ready.wait(timeout=5)


def _brush(hex_str):
    return SolidColorBrush(ColorConverter.ConvertFromString(hex_str))


def _restack():
    work = SystemParameters.WorkArea
    bottom = work.Bottom - _SCREEN_MARGIN
    for toast in _active_toasts:
        toast.Left = work.Right - _TOAST_WIDTH - _SCREEN_MARGIN
        toast.Top = bottom - toast.ActualHeight
        bottom -= toast.ActualHeight + _TOAST_GAP


def _dismiss(win):
    if win in _active_toasts:
        _active_toasts.remove(win)
    win.Close()
    _restack()


def _build_toast(conflict):
    severity = (conflict.get("severity") or "warning").lower()
    accent = _brush("#FFA000") if severity == "warning" else _brush("#D32F2F")
    bg = _brush("#1E1E1E")
    fg = _brush("#F5F5F5")
    sub = _brush("#B0B0B0")

    win = Window()
    win.Title = "RevitSync"
    win.Width = _TOAST_WIDTH
    win.SizeToContent = SizeToContent.Height
    win.WindowStyle = WindowStyle.None
    win.ResizeMode = ResizeMode.NoResize
    win.AllowsTransparency = True
    win.Background = Brushes.Transparent
    win.Topmost = True
    win.ShowInTaskbar = False
    win.Focusable = False
    win.WindowStartupLocation = WindowStartupLocation.Manual

    border = Border()
    border.Background = bg
    border.CornerRadius = CornerRadius(8)
    border.Padding = Thickness(14, 12, 14, 12)
    border.BorderBrush = accent
    border.BorderThickness = Thickness(0, 0, 0, 3)

    panel = StackPanel()
    panel.Orientation = Orientation.Vertical

    header = StackPanel()
    header.Orientation = Orientation.Horizontal
    header.Margin = Thickness(0, 0, 0, 6)

    badge = TextBlock()
    badge.Text = severity.upper()
    badge.Foreground = accent
    badge.FontWeight = FontWeights.Bold
    badge.FontSize = 11
    badge.Margin = Thickness(0, 0, 8, 0)

    title = TextBlock()
    title.Text = "RevitSync"
    title.Foreground = sub
    title.FontSize = 11

    header.Children.Add(badge)
    header.Children.Add(title)

    msg = TextBlock()
    msg.Text = conflict.get("plain_english") or "A conflict was detected."
    msg.Foreground = fg
    msg.FontSize = 13
    msg.TextWrapping = TextWrapping.Wrap
    msg.Margin = Thickness(0, 0, 0, 6)

    panel.Children.Add(header)
    panel.Children.Add(msg)

    suggestion_text = conflict.get("suggestion") or ""
    if suggestion_text:
        suggestion = TextBlock()
        suggestion.Text = suggestion_text
        suggestion.Foreground = sub
        suggestion.FontSize = 12
        suggestion.TextWrapping = TextWrapping.Wrap
        suggestion.FontStyle = FontStyles.Italic
        panel.Children.Add(suggestion)

    border.Child = panel
    win.Content = border

    timer = DispatcherTimer()
    timer.Interval = TimeSpan.FromSeconds(TOAST_LIFETIME_S)

    def on_tick(s, e):
        timer.Stop()
        _dismiss(win)

    def on_click(s, e):
        timer.Stop()
        _dismiss(win)

    timer.Tick += on_tick
    border.MouseLeftButtonUp += on_click
    timer.Start()

    return win


def _show_on_ui_thread(conflict):
    win = _build_toast(conflict)
    _active_toasts.insert(0, win)
    win.Show()
    win.UpdateLayout()
    _restack()


def show(conflict: dict):
    """Thread-safe entry point. Schedules the toast on the dispatcher thread."""
    _ensure_dispatcher()
    if _dispatcher is None:
        return
    _dispatcher.BeginInvoke(Action(lambda: _show_on_ui_thread(conflict)))
