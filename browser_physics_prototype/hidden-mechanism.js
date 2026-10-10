// Stable, learnable hidden law. Inputs are world-time only, not randomized per player.
// Deliberately export a deterministic function for testing; the player sees only measurements.
export function resonanceAt(seconds){if(!Number.isFinite(seconds)||seconds<0)throw Error('Invalid game time');return .63*Math.sin((2*Math.PI*seconds)/8.2+.18)+.37*Math.sin((2*Math.PI*seconds)/3.1+.95);}
export function measureResonance(seconds,previous=null){const intensity=Math.round(100*resonanceAt(seconds));const trend=previous===null?'unknown':intensity>previous?'rising':intensity<previous?'falling':'steady';return {intensity,trend,time:Math.round(seconds*10)/10};}
export function attemptResonance(seconds){const strength=resonanceAt(seconds);return {success:strength>=.66,intensity:Math.round(strength*100),time:seconds};}
