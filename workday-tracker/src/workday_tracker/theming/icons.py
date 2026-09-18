"""Small flat vector icons drawn at runtime with QPainter (no icon assets).

Each icon is drawn in a single color so it can be re-tinted to match the
active palette's button text color and stay readable in every theme.
"""

from __future__ import annotations

import math

from PySide6.QtCore import QPointF, Qt
from PySide6.QtGui import QColor, QIcon, QPainter, QPen, QPixmap, QPolygonF

_KINDS = ("edit", "delete", "new_message", "settings", "close", "info")


def make_icon(kind: str, color: str, size: int = 18) -> QIcon:
    """Render a small monochrome icon of the given kind and color."""
    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.GlobalColor.transparent)

    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    pen_color = QColor(color)
    pen = QPen(pen_color, max(1.4, size * 0.1))
    pen.setCapStyle(Qt.PenCapStyle.RoundCap)
    pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
    painter.setPen(pen)
    painter.setBrush(Qt.BrushStyle.NoBrush)

    margin = size * 0.2
    if kind == "edit":
        _draw_edit(painter, size, margin, pen_color)
    elif kind == "delete":
        _draw_delete(painter, size, margin)
    elif kind == "new_message":
        _draw_plus(painter, size, margin)
    elif kind == "settings":
        _draw_gear(painter, size, margin, pen_color)
    elif kind == "close":
        _draw_close(painter, size, margin)
    elif kind == "info":
        _draw_info(painter, size, margin, pen_color)
    else:
        raise ValueError(f"Unknown icon kind: {kind!r} (expected one of {_KINDS})")

    painter.end()
    return QIcon(pixmap)


def _draw_edit(painter: QPainter, size: float, margin: float, color: QColor) -> None:
    # A diagonal stroke (the pencil shaft) with a small filled nib at the tip.
    start = QPointF(margin, size - margin)
    end = QPointF(size - margin * 1.3, margin * 1.3)
    painter.drawLine(start, end)

    painter.setPen(Qt.PenStyle.NoPen)
    painter.setBrush(color)
    nib_size = size * 0.16
    nib = QPolygonF(
        [
            end,
            QPointF(end.x() - nib_size, end.y()),
            QPointF(end.x(), end.y() + nib_size),
        ]
    )
    painter.drawPolygon(nib)


def _draw_delete(painter: QPainter, size: float, margin: float) -> None:
    top = margin * 0.9
    left = margin
    right = size - margin
    bottom = size - margin * 0.8

    # Lid.
    painter.drawLine(QPointF(left, top), QPointF(right, top))
    lid_w = (right - left) * 0.35
    center_x = (left + right) / 2
    painter.drawLine(
        QPointF(center_x - lid_w / 2, top), QPointF(center_x - lid_w / 2 - size * 0.05, top - size * 0.1)
    )
    painter.drawLine(
        QPointF(center_x + lid_w / 2, top), QPointF(center_x + lid_w / 2 + size * 0.05, top - size * 0.1)
    )

    # Bin body (trapezoid, slightly narrower at the bottom).
    inset = size * 0.06
    body = QPolygonF(
        [
            QPointF(left + size * 0.02, top),
            QPointF(right - size * 0.02, top),
            QPointF(right - inset, bottom),
            QPointF(left + inset, bottom),
        ]
    )
    painter.drawPolygon(body)

    # Two vertical ribs inside the bin.
    rib_top = top + size * 0.12
    rib_bottom = bottom - size * 0.08
    for fraction in (0.38, 0.62):
        x = left + (right - left) * fraction
        painter.drawLine(QPointF(x, rib_top), QPointF(x, rib_bottom))


def _draw_plus(painter: QPainter, size: float, margin: float) -> None:
    mid = size / 2
    painter.drawLine(QPointF(mid, margin), QPointF(mid, size - margin))
    painter.drawLine(QPointF(margin, mid), QPointF(size - margin, mid))


def _draw_gear(painter: QPainter, size: float, margin: float, color: QColor) -> None:
    center = QPointF(size / 2, size / 2)
    outer_r = size / 2 - margin * 0.6
    inner_r = outer_r * 0.55
    tooth_len = size * 0.11

    tooth_count = 8
    for i in range(tooth_count):
        angle = (2 * math.pi / tooth_count) * i
        x1 = center.x() + outer_r * math.cos(angle)
        y1 = center.y() + outer_r * math.sin(angle)
        x2 = center.x() + (outer_r + tooth_len) * math.cos(angle)
        y2 = center.y() + (outer_r + tooth_len) * math.sin(angle)
        painter.drawLine(QPointF(x1, y1), QPointF(x2, y2))

    painter.drawEllipse(center, outer_r, outer_r)
    painter.setPen(Qt.PenStyle.NoPen)
    painter.setBrush(color)
    painter.drawEllipse(center, inner_r * 0.4, inner_r * 0.4)


def _draw_close(painter: QPainter, size: float, margin: float) -> None:
    painter.drawLine(QPointF(margin, margin), QPointF(size - margin, size - margin))
    painter.drawLine(QPointF(size - margin, margin), QPointF(margin, size - margin))


def _draw_info(painter: QPainter, size: float, margin: float, color: QColor) -> None:
    center = QPointF(size / 2, size / 2)
    radius = size / 2 - margin * 0.6
    painter.drawEllipse(center, radius, radius)

    painter.setPen(Qt.PenStyle.NoPen)
    painter.setBrush(color)
    dot_radius = size * 0.07
    painter.drawEllipse(QPointF(center.x(), size * 0.32), dot_radius, dot_radius)

    stem_pen = QPen(color, max(1.4, size * 0.12))
    stem_pen.setCapStyle(Qt.PenCapStyle.RoundCap)
    painter.setPen(stem_pen)
    painter.drawLine(QPointF(center.x(), size * 0.46), QPointF(center.x(), size * 0.72))
