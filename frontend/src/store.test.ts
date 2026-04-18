import { describe, it, expect, vi, beforeEach } from 'vitest';
import { useAppStore } from './store';
import * as idb from './lib/idb';
import type { PendingReport } from './lib/idb';

vi.mock('./lib/idb', async () => {
  return {
    attachmentToFile: vi.fn((attachment: { blob: Blob; name: string; type: string }, fallbackName: string) => (
      new File([attachment.blob], attachment.name || fallbackName, { type: attachment.type })
    )),
    getPendingReports: vi.fn(),
    deleteReportOffline: vi.fn(),
  };
});

describe('AppStore', () => {
  const fetchMock = vi.fn<typeof fetch>();
  const alertMock = vi.fn<typeof alert>();

  beforeEach(() => {
    vi.clearAllMocks();
    useAppStore.setState({ isOnline: true, queueCount: 0 });
    Object.defineProperty(globalThis, 'fetch', {
      configurable: true,
      writable: true,
      value: fetchMock,
    });
    Object.defineProperty(globalThis, 'alert', {
      configurable: true,
      writable: true,
      value: alertMock,
    });
  });

  it('flushQueue sends queued reports and deletes them', async () => {
    const mockReports: PendingReport[] = [
      {
        id: 1,
        site_id: 'test-site',
        reporter_name: 'Test',
        reporter_role: 'Role',
        transcript_text: 'Text',
        photo_attachment: {
          blob: new Blob(['photo-bytes'], { type: 'image/jpeg' }),
          name: 'flood.jpg',
          type: 'image/jpeg',
        },
        audio_attachment: {
          blob: new Blob(['audio-bytes'], { type: 'audio/mpeg' }),
          name: 'note.mp3',
          type: 'audio/mpeg',
        },
        offline_created: true,
        createdAt: 123,
      },
    ];

    vi.mocked(idb.getPendingReports).mockResolvedValue(mockReports);
    
    fetchMock.mockResolvedValue({
      ok: true,
      json: async () => ({ id: 1 }),
    } as Response);

    await useAppStore.getState().flushQueue();

    expect(fetchMock).toHaveBeenCalledTimes(2);
    const reportCall = fetchMock.mock.calls[0];
    expect(reportCall[0]).toContain('/api/reports');

    const formData = reportCall[1]?.body as FormData;
    expect(formData.get('site_id')).toBe('test-site');
    expect(formData.get('transcript_text')).toBe('Text');
    expect(formData.get('offline_created')).toBe('true');
    expect(formData.get('photo')).toBeInstanceOf(File);
    expect((formData.get('photo') as File).name).toBe('flood.jpg');
    expect(formData.get('audio')).toBeInstanceOf(File);
    expect((formData.get('audio') as File).name).toBe('note.mp3');
    expect(fetchMock.mock.calls[1][0]).toContain('/api/sync/flush');
    expect(idb.deleteReportOffline).toHaveBeenCalledWith(1);
  });

  it('flushQueue does nothing if offline', async () => {
    useAppStore.setState({ isOnline: false });
    await useAppStore.getState().flushQueue();
    expect(fetchMock).not.toHaveBeenCalled();
    expect(alertMock).toHaveBeenCalledWith('Cannot flush queue while offline');
  });
});
