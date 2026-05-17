import base64
import io
import logging
import math

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

try:
    from PIL import Image, ImageDraw, ImageEnhance
    import av
    _MEDIA_LIBS_AVAILABLE = True
except ImportError:
    _MEDIA_LIBS_AVAILABLE = False
    Image = ImageDraw = ImageEnhance = av = None  # type: ignore[assignment]

logger = logging.getLogger(__name__)
router = APIRouter()


class AnimatedGifRequest(BaseModel):
    image_data_url: str = Field(..., min_length=32)
    width: int = Field(default=720, ge=240, le=1080)
    height: int = Field(default=900, ge=240, le=1350)
    frame_count: int = Field(default=24, ge=8, le=48)
    duration_ms: int = Field(default=4200, ge=1000, le=12000)


def _decode_data_url(data_url: str) -> bytes:
    if not data_url.startswith('data:image/') or ',' not in data_url:
        raise ValueError('Expected an image data URL')
    _, encoded = data_url.split(',', 1)
    return base64.b64decode(encoded)


def _resize_cover(image: Image.Image, target_width: int, target_height: int) -> Image.Image:
    source_width, source_height = image.size
    if source_width <= 0 or source_height <= 0:
        raise ValueError('Invalid source image dimensions')

    scale = max(target_width / source_width, target_height / source_height)
    resized = image.resize((max(1, int(round(source_width * scale))), max(1, int(round(source_height * scale)))), Image.Resampling.LANCZOS)

    left = max(0, (resized.width - target_width) // 2)
    top = max(0, (resized.height - target_height) // 2)
    return resized.crop((left, top, left + target_width, top + target_height))


def _build_frames(base_image: Image.Image, frame_count: int) -> list[Image.Image]:
    width, height = base_image.size
    frames: list[Image.Image] = []

    for index in range(frame_count):
        progress = index / frame_count
        phase = progress * math.tau
        scale = 1.0 + (0.018 * math.sin(phase))
        drift_x = int(round(math.sin(phase * 0.7) * 14))
        drift_y = int(round(math.cos(phase * 0.55) * 10))

        scaled_width = max(width + 24, int(round(width * scale)))
        scaled_height = max(height + 24, int(round(height * scale)))
        scaled = base_image.resize((scaled_width, scaled_height), Image.Resampling.LANCZOS)

        frame = Image.new('RGBA', (width, height), (10, 8, 6, 255))
        paste_x = (width - scaled_width) // 2 + drift_x
        paste_y = (height - scaled_height) // 2 + drift_y
        frame.paste(scaled, (paste_x, paste_y), scaled)

        overlay = Image.new('RGBA', (width, height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(overlay, 'RGBA')

        sweep_x = int(round((progress * (width + 420)) - 210))
        draw.rectangle((sweep_x - 140, 0, sweep_x + 140, height), fill=(255, 244, 214, 24))
        draw.ellipse((int(width * 0.07), int(height * 0.10), int(width * 0.07) + 260, int(height * 0.10) + 260), fill=(255, 198, 126, 26))
        draw.ellipse((int(width * 0.76), int(height * 0.66), int(width * 0.76) + 280, int(height * 0.66) + 280), fill=(116, 210, 255, 18))

        frame = Image.alpha_composite(frame, overlay)
        contrast = ImageEnhance.Contrast(frame).enhance(1.02)
        brightness = ImageEnhance.Brightness(contrast).enhance(1.01)
        frames.append(brightness.convert('RGB').quantize(colors=256, method=Image.Quantize.MEDIANCUT))

    return frames


def _build_frames_rgb(base_image: Image.Image, frame_count: int) -> list[Image.Image]:
    width, height = base_image.size
    frames: list[Image.Image] = []

    for index in range(frame_count):
        progress = index / frame_count
        phase = progress * math.tau
        scale = 1.0 + (0.018 * math.sin(phase))
        drift_x = int(round(math.sin(phase * 0.7) * 14))
        drift_y = int(round(math.cos(phase * 0.55) * 10))

        scaled_width = max(width + 24, int(round(width * scale)))
        scaled_height = max(height + 24, int(round(height * scale)))
        scaled = base_image.resize((scaled_width, scaled_height), Image.Resampling.LANCZOS)

        frame = Image.new('RGBA', (width, height), (10, 8, 6, 255))
        paste_x = (width - scaled_width) // 2 + drift_x
        paste_y = (height - scaled_height) // 2 + drift_y
        frame.paste(scaled, (paste_x, paste_y), scaled)

        overlay = Image.new('RGBA', (width, height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(overlay, 'RGBA')

        sweep_x = int(round((progress * (width + 420)) - 210))
        draw.rectangle((sweep_x - 140, 0, sweep_x + 140, height), fill=(255, 244, 214, 24))
        draw.ellipse((int(width * 0.07), int(height * 0.10), int(width * 0.07) + 260, int(height * 0.10) + 260), fill=(255, 198, 126, 26))
        draw.ellipse((int(width * 0.76), int(height * 0.66), int(width * 0.76) + 280, int(height * 0.66) + 280), fill=(116, 210, 255, 18))

        frame = Image.alpha_composite(frame, overlay)
        contrast = ImageEnhance.Contrast(frame).enhance(1.02)
        brightness = ImageEnhance.Brightness(contrast).enhance(1.01)
        frames.append(brightness.convert('RGB'))

    return frames


def _encode_h264_mp4(frames: list[Image.Image], fps: int) -> io.BytesIO:
    if not frames:
        raise ValueError('No frames available for MP4 encoding')

    width, height = frames[0].size
    output = io.BytesIO()
    container = av.open(output, mode='w', format='mp4')
    stream = container.add_stream('libx264', rate=fps)
    stream.width = width
    stream.height = height
    stream.pix_fmt = 'yuv420p'
    stream.options = {
        'preset': 'veryfast',
        'crf': '23',
        'movflags': 'faststart',
    }

    for image in frames:
        video_frame = av.VideoFrame.from_image(image)
        for packet in stream.encode(video_frame):
            container.mux(packet)

    for packet in stream.encode(None):
        container.mux(packet)

    container.close()
    output.seek(0)
    return output


@router.post('/api/share/animated-gif')
def build_animated_gif(payload: AnimatedGifRequest):
    if not _MEDIA_LIBS_AVAILABLE:
        raise HTTPException(status_code=503, detail='Animated export is not available on this server')
    try:
        raw_image = _decode_data_url(payload.image_data_url)
        with Image.open(io.BytesIO(raw_image)) as source_image:
            base_image = source_image.convert('RGBA')
            fitted = _resize_cover(base_image, payload.width, payload.height)
            frames = _build_frames(fitted, payload.frame_count)

        buffer = io.BytesIO()
        frame_duration = max(40, int(round(payload.duration_ms / payload.frame_count)))
        frames[0].save(
            buffer,
            format='GIF',
            save_all=True,
            append_images=frames[1:],
            duration=frame_duration,
            loop=0,
            disposal=2,
            optimize=True,
        )
        buffer.seek(0)

        return StreamingResponse(
            buffer,
            media_type='image/gif',
            headers={
                'Content-Disposition': 'attachment; filename=mirror-talk-motion.gif',
                'Cache-Control': 'no-store',
            },
        )
    except Exception as exc:
        logger.exception('Failed to generate animated GIF')
        raise HTTPException(status_code=500, detail='Unable to generate animated GIF') from exc


@router.post('/api/share/animated-mp4')
def build_animated_mp4(payload: AnimatedGifRequest):
    if not _MEDIA_LIBS_AVAILABLE:
        raise HTTPException(status_code=503, detail='Animated export is not available on this server')
    try:
        raw_image = _decode_data_url(payload.image_data_url)
        with Image.open(io.BytesIO(raw_image)) as source_image:
            base_image = source_image.convert('RGBA')
            fitted = _resize_cover(base_image, payload.width, payload.height)
            rgb_frames = _build_frames_rgb(fitted, payload.frame_count)

        fps = max(6, int(round(payload.frame_count / max(payload.duration_ms / 1000.0, 0.1))))
        buffer = _encode_h264_mp4(rgb_frames, fps)

        return StreamingResponse(
            buffer,
            media_type='video/mp4',
            headers={
                'Content-Disposition': 'attachment; filename=mirror-talk-motion.mp4',
                'Cache-Control': 'no-store',
            },
        )
    except Exception as exc:
        logger.exception('Failed to generate animated MP4')
        raise HTTPException(status_code=500, detail='Unable to generate animated MP4') from exc