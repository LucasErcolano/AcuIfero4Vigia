from __future__ import annotations

import tempfile
from pathlib import Path

import cv2
import httpx
import numpy as np

API_URL = 'http://localhost:8000/api'


def build_demo_video(path: Path) -> None:
    width, height = 320, 240
    writer = cv2.VideoWriter(str(path), cv2.VideoWriter_fourcc(*'MJPG'), 4.0, (width, height))
    if not writer.isOpened():
        raise RuntimeError('Could not create demo video')

    for index in range(16):
        frame = np.full((height, width, 3), (210, 215, 225), dtype=np.uint8)
        waterline_y = max(75, 210 - index * 9)
        cv2.rectangle(frame, (0, waterline_y), (width - 1, height - 1), (90, 70, 40), -1)
        cv2.line(frame, (0, 100), (width - 1, 100), (245, 245, 245), 2)
        writer.write(frame)

    writer.release()


print('--- Acuifero 4 + Vigia Demo Script ---')

with tempfile.TemporaryDirectory() as temp_dir:
    video_path = Path(temp_dir) / 'node-demo.avi'
    build_demo_video(video_path)

    print('\n1. Running bundled Silverado sample clip...')
    sample_response = httpx.post(f'{API_URL}/sites/silverado-fixed-cam-usgs/sample-node-analysis', timeout=90)
    if sample_response.is_success:
        sample_payload = sample_response.json()
        print(
            'Bundled sample alert:',
            sample_payload['alert']['level'],
            f"score={sample_payload['alert']['score']:.2f}",
        )
    else:
        print(f'Sample clip skipped: {sample_response.status_code} {sample_response.text}')

    print('\n2. Refreshing live hydromet snapshot...')
    hydromet_response = httpx.post(f'{API_URL}/sites/puente-arroyo-01/external-snapshot/refresh', timeout=30)
    if hydromet_response.is_success:
        hydromet_payload = hydromet_response.json()
        print(f"Hydromet signal score: {hydromet_payload['signal_score']:.2f}")
    else:
        print(f'Hydromet refresh skipped: {hydromet_response.status_code} {hydromet_response.text}')

    print('\n3. Triggering fixed-node video analysis with a generated clip...')
    with video_path.open('rb') as handle:
        node_response = httpx.post(
            f'{API_URL}/node/analyze',
            data={'site_id': 'puente-arroyo-01'},
            files={'video': (video_path.name, handle, 'video/x-msvideo')},
            timeout=60,
        )
    node_response.raise_for_status()
    node_payload = node_response.json()
    print(f"Node alert level: {node_payload['alert']['level']} | score={node_payload['alert']['score']:.2f}")

    print('\n4. Sending volunteer report...')
    report_response = httpx.post(
        f'{API_URL}/reports',
        data={
            'site_id': 'puente-arroyo-01',
            'reporter_name': 'Juan Demo',
            'reporter_role': 'Bombero',
            'transcript_text': 'El agua ya paso la marca critica del puente y la calle esta cortada',
            'offline_created': 'true',
        },
        timeout=30,
    )
    report_response.raise_for_status()
    report_payload = report_response.json()
    print(f"Structured parser source: {report_payload['parsed']['parser_source']}")
    print(f"Fused alert after report: {report_payload['alert']['level']} | score={report_payload['alert']['score']:.2f}")

    print('\n5. Flushing edge sync queue into central.db...')
    sync_response = httpx.post(f'{API_URL}/sync/flush', timeout=30)
    sync_response.raise_for_status()
    print(sync_response.json())

print('\nDemo complete. Open http://localhost:5173 and inspect the dashboard/site detail pages.')
