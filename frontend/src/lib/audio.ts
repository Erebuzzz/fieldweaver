let audioCtx: AudioContext | null = null;
const STORAGE_KEY = "fieldweaver_audio_muted";

function getAudioContext(): AudioContext | null {
  if (typeof window === "undefined") {
    return null;
  }
  if (!audioCtx) {
    const AudioContextClass = window.AudioContext || (window as unknown as { webkitAudioContext: typeof AudioContext }).webkitAudioContext;
    if (AudioContextClass) {
      audioCtx = new AudioContextClass();
    }
  }
  return audioCtx;
}

export function isMuted(): boolean {
  if (typeof window === "undefined") {
    return true;
  }
  try {
    const val = localStorage.getItem(STORAGE_KEY);
    return val === "true";
  } catch {
    return false;
  }
}

export function setMuted(muted: boolean): void {
  if (typeof window === "undefined") {
    return;
  }
  try {
    localStorage.setItem(STORAGE_KEY, muted ? "true" : "false");
  } catch {
    // Ignore storage quota or access errors
  }
}

export function toggleMute(): boolean {
  const next = !isMuted();
  setMuted(next);
  return next;
}

export function playPlumeDetectionPing(intensity = 0.5): void {
  if (isMuted()) {
    return;
  }
  const ctx = getAudioContext();
  if (!ctx) {
    return;
  }
  if (ctx.state === "suspended") {
    ctx.resume().catch(() => {});
  }

  const now = ctx.currentTime;
  const clampedIntensity = Math.max(0, Math.min(1, intensity));
  const carrierFreq = 960 + 480 * clampedIntensity;

  const osc = ctx.createOscillator();
  const harmonic = ctx.createOscillator();
  const filter = ctx.createBiquadFilter();
  const gain = ctx.createGain();

  filter.type = "bandpass";
  filter.frequency.setValueAtTime(carrierFreq, now);
  filter.Q.setValueAtTime(3.0, now);

  osc.type = "sine";
  osc.frequency.setValueAtTime(carrierFreq, now);

  harmonic.type = "sine";
  harmonic.frequency.setValueAtTime(carrierFreq * 2, now);

  gain.gain.setValueAtTime(0.0001, now);
  gain.gain.linearRampToValueAtTime(0.06 + 0.03 * clampedIntensity, now + 0.003);
  gain.gain.exponentialRampToValueAtTime(0.0001, now + 0.09);

  osc.connect(filter);
  harmonic.connect(filter);
  filter.connect(gain);
  gain.connect(ctx.destination);

  osc.start(now);
  harmonic.start(now);
  osc.stop(now + 0.1);
  harmonic.stop(now + 0.1);
}

export function playSafetyInterventionClick(): void {
  if (isMuted()) {
    return;
  }
  const ctx = getAudioContext();
  if (!ctx) {
    return;
  }
  if (ctx.state === "suspended") {
    ctx.resume().catch(() => {});
  }

  const now = ctx.currentTime;
  const osc = ctx.createOscillator();
  const filter = ctx.createBiquadFilter();
  const gain = ctx.createGain();

  osc.type = "triangle";
  osc.frequency.setValueAtTime(220, now);
  osc.frequency.exponentialRampToValueAtTime(55, now + 0.03);

  filter.type = "lowpass";
  filter.frequency.setValueAtTime(240, now);
  filter.Q.setValueAtTime(4.0, now);

  gain.gain.setValueAtTime(0.0001, now);
  gain.gain.linearRampToValueAtTime(0.12, now + 0.002);
  gain.gain.exponentialRampToValueAtTime(0.0001, now + 0.035);

  osc.connect(filter);
  filter.connect(gain);
  gain.connect(ctx.destination);

  osc.start(now);
  osc.stop(now + 0.04);
}
