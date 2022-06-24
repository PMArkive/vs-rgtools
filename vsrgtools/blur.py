from __future__ import annotations

__all__ = [
    'sbr', 'min_blur', 'box_blur', 'blur'
]


from functools import partial
from typing import Sequence

import vapoursynth as vs
from vsutil import disallow_variable_format, disallow_variable_resolution, get_neutral_value

from .enum import ConvMode
from .util import mean_matrix, normalise_planes, normalise_seq, wmean_matrix

core = vs.core


@disallow_variable_format
@disallow_variable_resolution
def blur(
    clip: vs.VideoNode,
    radius: int = 1, mode: ConvMode = ConvMode.SQUARE,
    planes: int | Sequence[int] | None = None
) -> vs.VideoNode:
    assert clip.format

    planes = normalise_planes(clip, planes)

    if mode == ConvMode.SQUARE:
        matrix2 = [1, 3, 4, 3, 1]
        matrix3 = [1, 4, 8, 10, 8, 4, 1]
    elif mode in {ConvMode.HORIZONTAL, ConvMode.VERTICAL}:
        matrix2 = [1, 6, 15, 20, 15, 6, 1]
        matrix3 = [1, 10, 45, 120, 210, 252, 210, 120, 45, 10, 1]
    else:
        raise ValueError('blur: invalid mode specified!')

    if radius == 1:
        matrix = [1, 2, 1]
    elif radius == 2:
        matrix = matrix2
    elif radius == 3:
        matrix = matrix3
    else:
        raise ValueError('blur: invalid radius')

    return clip.std.Convolution(matrix, planes=planes, mode=mode)


@disallow_variable_format
@disallow_variable_resolution
def box_blur(
    clip: vs.VideoNode, weights: Sequence[float], planes: int | Sequence[int] | None = None
) -> vs.VideoNode:
    assert clip.format

    if len(weights) != 9:
        raise ValueError('box_blur: weights has to be an array of length 9!')

    try:
        aka_expr = core.akarin.Expr
    except AttributeError:
        pass
    else:
        weights_string = ' '.join([
            x.format(w=w) for x, w in zip([
                'x[-1,-1] {w} *', 'x[0,-1] {w} *', 'x[1,-1] {w} *',
                'x[-1,0] {w} *', 'x {w} *', 'x[1,0] {w} *',
                'x[-1,1] {w} *', 'x[0,1] {w} *', 'x[1,1] {w} *'
            ], weights)
        ])

        add_string = '+ ' * 8

        expr_string = f'{weights_string} {add_string} {sum(map(float, weights))} /'

        return aka_expr(clip, [
            expr_string if i in normalise_planes(clip, planes) else ''
            for i in range(clip.format.num_planes)
        ])
    return clip.std.Convolution(weights, planes=planes)


@disallow_variable_format
@disallow_variable_resolution
def min_blur(clip: vs.VideoNode, radius: int = 1, planes: int | Sequence[int] | None = None) -> vs.VideoNode:
    """
    MinBlur   by Didée (http://avisynth.nl/index.php/MinBlur)
    Nifty Gauss/Median combination
    """
    assert clip.format

    planes = normalise_planes(clip, planes)
    pbox_blur = partial(box_blur, planes=planes)

    median = clip.std.Median(planes) if radius in {0, 1} else clip.ctmf.CTMF(radius, planes=planes)

    if radius == 0:
        weighted = sbr(clip, planes=planes)
    elif radius == 1:
        weighted = pbox_blur(clip, wmean_matrix)
    elif radius == 2:
        weighted = pbox_blur(pbox_blur(clip, wmean_matrix), mean_matrix)
    else:
        weighted = pbox_blur(pbox_blur(pbox_blur(clip, wmean_matrix), mean_matrix), mean_matrix)

    return core.std.Expr([clip, weighted, median], [
        'x y - x z - * 0 < x x y - abs x z - abs < y z ? ?'
        if i in planes else '' for i in range(clip.format.num_planes)
    ])


@disallow_variable_format
@disallow_variable_resolution
def sbr(
    clip: vs.VideoNode,
    radius: int = 1, mode: ConvMode = ConvMode.SQUARE,
    planes: int | Sequence[int] | None = None
) -> vs.VideoNode:
    assert clip.format

    planes = normalise_planes(clip, planes)

    neutral = normalise_seq(
        [get_neutral_value(clip), get_neutral_value(clip, True)], clip.format.num_planes
    )

    blur_func = partial(blur, radius=radius, mode=mode, planes=planes)

    weighted = blur_func(clip)

    diff = clip.std.MakeDiff(weighted, planes)

    diff_weighted = blur_func(diff)

    diff = core.std.Expr([diff, diff_weighted], [
        f'x y - x {mid} - * 0 < {mid} x y - abs x {mid} - abs < x y - {mid} + x ? ?'
        if i in planes else '' for i, mid in enumerate(neutral, 0)
    ])

    return clip.std.MakeDiff(diff, planes)