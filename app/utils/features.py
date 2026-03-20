import math

def month_features(month):
    sin = math.sin(2 * math.pi * month / 12)
    cos = math.cos(2 * math.pi * month / 12)
    return sin, cos