export interface AppConfig {
  pageTitle: string;
  pageDescription: string;
  companyName: string;

  supportsChatInput: boolean;
  supportsVideoInput: boolean;
  supportsScreenShare: boolean;
  isPreConnectBufferEnabled: boolean;

  logo: string;
  startButtonText: string;
  accent?: string;
  logoDark?: string;
  accentDark?: string;

  audioVisualizerType?: 'bar' | 'wave' | 'grid' | 'radial' | 'aura';
  audioVisualizerColor?: `#${string}`;
  audioVisualizerColorDark?: `#${string}`;
  audioVisualizerColorShift?: number;
  audioVisualizerBarCount?: number;
  audioVisualizerGridRowCount?: number;
  audioVisualizerGridColumnCount?: number;
  audioVisualizerRadialBarCount?: number;
  audioVisualizerRadialRadius?: number;
  audioVisualizerWaveLineWidth?: number;

  // agent dispatch configuration
  agentName?: string;

  // LiveKit Cloud Sandbox configuration
  sandboxId?: string;
}

export const APP_CONFIG_DEFAULTS: AppConfig = {
  companyName: 'KRN Agent',
  pageTitle: 'KRN Agent · Dein digitaler Assistent',
  pageDescription: 'Natürlich sprechen. Gemeinsam sehen. Einfach erledigen.',

  supportsChatInput: true,
  supportsVideoInput: true,
  supportsScreenShare: true,
  isPreConnectBufferEnabled: false,

  logo: '/krn-mark.svg',
  accent: '#087f8c',
  logoDark: '/krn-mark.svg',
  accentDark: '#58e4ce',
  startButtonText: 'Gespräch starten',

  // optional: audio visualization configuration
  // audioVisualizerType: 'bar',
  audioVisualizerColor: '#087f8c',
  audioVisualizerColorDark: '#58e4ce',
  // audioVisualizerColorShift: 0.3,
  // audioVisualizerBarCount: 5,
  //audioVisualizerType: 'radial',
  //audioVisualizerRadialBarCount: 24,
  //audioVisualizerRadialRadius: 100,
  //audioVisualizerType: 'grid',
  //audioVisualizerGridRowCount: 25,
  //audioVisualizerGridColumnCount: 25,
  //audioVisualizerType: 'wave',
  //audioVisualizerWaveLineWidth: 3,
  audioVisualizerType: 'aura',

  // agent dispatch configuration
  agentName: process.env.AGENT_NAME ?? 'my-agent',

  // LiveKit Cloud Sandbox configuration
  sandboxId: undefined,
};
