import { useEffect, useRef } from 'react';
import { tokens, font, WHEEL_NUMBERS, getColor } from '@/tokens';

interface RouletteWheelProps {
  spinning: boolean;
  resultNumber: number | null;
  size?: number;
}

const SEG_ANGLE = (Math.PI * 2) / 37;
// Pointer is at top = -PI/2 in canvas coordinates
const POINTER_ANGLE = -Math.PI / 2;

/**
 * Calculate the target wheel angle so that the given number's segment
 * center sits directly under the pointer (top of wheel).
 */
function getTargetAngle(num: number, currentAngle: number): number {
  const idx = WHEEL_NUMBERS.indexOf(num);
  if (idx === -1) return currentAngle;

  // The center of segment `idx` is at: angleRef + idx * SEG_ANGLE + SEG_ANGLE/2
  // We need: angleRef + idx * SEG_ANGLE + SEG_ANGLE/2 = POINTER_ANGLE (mod 2PI)
  // So: angleRef = POINTER_ANGLE - idx * SEG_ANGLE - SEG_ANGLE/2
  const baseTarget = POINTER_ANGLE - idx * SEG_ANGLE - SEG_ANGLE / 2;

  // Ensure we spin forward (positive direction) at least 3 full rotations
  // from the current angle for a nice visual effect
  const fullRotations = Math.PI * 2 * 3;
  let target = baseTarget;
  while (target < currentAngle + fullRotations) {
    target += Math.PI * 2;
  }
  return target;
}

export function RouletteWheel({ spinning, resultNumber, size = 320 }: RouletteWheelProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const animRef = useRef<number>(0);
  const angleRef = useRef(0);
  const spinningRef = useRef(false);
  const targetAngleRef = useRef<number | null>(null);
  const spinStartTimeRef = useRef(0);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    canvas.width = size * 2;
    canvas.height = size * 2;
    ctx.scale(2, 2);
    const cx = size / 2, cy = size / 2, r = size / 2 - 10;

    function draw() {
      ctx!.clearRect(0, 0, size, size);

      // Outer glow
      const glow = ctx!.createRadialGradient(cx, cy, r - 5, cx, cy, r + 10);
      glow.addColorStop(0, 'rgba(240,194,70,0.08)');
      glow.addColorStop(1, 'transparent');
      ctx!.fillStyle = glow;
      ctx!.fillRect(0, 0, size, size);

      // Outer ring
      ctx!.beginPath();
      ctx!.arc(cx, cy, r + 2, 0, Math.PI * 2);
      ctx!.strokeStyle = tokens.accent.goldDim;
      ctx!.lineWidth = 2;
      ctx!.stroke();

      ctx!.beginPath();
      ctx!.arc(cx, cy, r, 0, Math.PI * 2);
      ctx!.fillStyle = '#0D0C14';
      ctx!.fill();

      // Number segments
      WHEEL_NUMBERS.forEach((num, i) => {
        const startA = angleRef.current + i * SEG_ANGLE;
        const endA = startA + SEG_ANGLE;
        ctx!.beginPath();
        ctx!.moveTo(cx, cy);
        ctx!.arc(cx, cy, r - 4, startA, endA);
        ctx!.closePath();
        ctx!.fillStyle = getColor(num);
        ctx!.fill();
        ctx!.strokeStyle = 'rgba(255,255,255,0.08)';
        ctx!.lineWidth = 0.5;
        ctx!.stroke();

        // Number text
        const midA = startA + SEG_ANGLE / 2;
        const tr = r - 22;
        const tx = cx + Math.cos(midA) * tr;
        const ty = cy + Math.sin(midA) * tr;
        ctx!.save();
        ctx!.translate(tx, ty);
        ctx!.rotate(midA + Math.PI / 2);
        ctx!.fillStyle = '#fff';
        ctx!.font = "bold 9px 'DM Sans', sans-serif";
        ctx!.textAlign = 'center';
        ctx!.fillText(num.toString(), 0, 0);
        ctx!.restore();
      });

      // Inner circle
      ctx!.beginPath();
      ctx!.arc(cx, cy, r * 0.55, 0, Math.PI * 2);
      const innerGrad = ctx!.createRadialGradient(cx, cy, 0, cx, cy, r * 0.55);
      innerGrad.addColorStop(0, '#1C1A30');
      innerGrad.addColorStop(1, '#0D0C14');
      ctx!.fillStyle = innerGrad;
      ctx!.fill();
      ctx!.strokeStyle = tokens.accent.goldDim;
      ctx!.lineWidth = 1;
      ctx!.stroke();

      // Center logo
      ctx!.fillStyle = tokens.accent.gold;
      ctx!.font = `bold 14px ${font.display}`;
      ctx!.textAlign = 'center';
      ctx!.textBaseline = 'middle';
      ctx!.fillText('ABC', cx, cy - 6);
      ctx!.fillStyle = tokens.text.muted;
      ctx!.font = `9px ${font.body}`;
      ctx!.fillText('BotChips', cx, cy + 10);

      // Ball marker (pointer at top)
      ctx!.beginPath();
      ctx!.moveTo(cx, cy - r + 2);
      ctx!.lineTo(cx - 6, cy - r - 8);
      ctx!.lineTo(cx + 6, cy - r - 8);
      ctx!.closePath();
      ctx!.fillStyle = tokens.accent.gold;
      ctx!.fill();

      // Animation logic
      if (targetAngleRef.current !== null) {
        // Easing towards target angle
        const target = targetAngleRef.current;
        const remaining = target - angleRef.current;
        if (Math.abs(remaining) < 0.001) {
          angleRef.current = target;
          targetAngleRef.current = null;
          spinningRef.current = false;
        } else {
          // Ease-out: move a fraction of the remaining distance
          angleRef.current += remaining * 0.04;
        }
      } else if (spinningRef.current) {
        // Free spin (constant speed) while waiting for result
        angleRef.current += 0.25;
      }

      animRef.current = requestAnimationFrame(draw);
    }
    draw();
    return () => cancelAnimationFrame(animRef.current);
  }, [size]);

  // Start spinning
  useEffect(() => {
    if (spinning) {
      spinningRef.current = true;
      targetAngleRef.current = null;
      spinStartTimeRef.current = Date.now();
    }
  }, [spinning]);

  // When result arrives and spinning stops, animate to target
  useEffect(() => {
    if (!spinning && resultNumber !== null) {
      targetAngleRef.current = getTargetAngle(resultNumber, angleRef.current);
    }
  }, [spinning, resultNumber]);

  const colorClass = resultNumber !== null
    ? resultNumber === 0 ? 'bg-roulette-green' : getColor(resultNumber) === tokens.roulette.red ? 'bg-roulette-red' : 'bg-roulette-black'
    : '';

  return (
    <div className="relative" style={{ width: size, height: size }}>
      <canvas ref={canvasRef} style={{ width: size, height: size }} />
      {resultNumber !== null && !spinning && (
        <div className={`absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 ${colorClass} border-2 border-gold rounded-xl px-5 py-3 text-center animate-fade-in`}
          style={{ boxShadow: `0 0 30px ${getColor(resultNumber)}88` }}>
          <div className="text-3xl font-extrabold text-white font-display">{resultNumber}</div>
          <div className="text-xs text-white/70 font-body">
            {resultNumber === 0 ? 'GREEN' : getColor(resultNumber) === tokens.roulette.red ? 'RED' : 'BLACK'}
          </div>
        </div>
      )}
    </div>
  );
}
