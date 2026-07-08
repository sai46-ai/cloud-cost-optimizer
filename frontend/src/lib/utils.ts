import { type ClassValue, clsx } from "clsx"
import { twMerge } from "tailwind-merge"

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

export function formatCurrency(value: number): string {
  try {
    const num = Number(value);
    if (isNaN(num)) return '$0.00';
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    }).format(num);
  } catch (e) {
    return '$0.00';
  }
}

export function formatNumber(value: number): string {
  try {
    const num = Number(value);
    if (isNaN(num)) return '0';
    return new Intl.NumberFormat('en-US').format(num);
  } catch (e) {
    return '0';
  }
}

export function formatDate(dateString: string): string {
  try {
    if (!dateString) return 'N/A';
    const date = new Date(dateString);
    if (isNaN(date.getTime())) return 'N/A';
    return new Intl.DateTimeFormat('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric'
    }).format(date);
  } catch (e) {
    return 'N/A';
  }
}

export function isWebGLAvailable(): boolean {
  if (typeof window !== 'undefined' && (navigator.webdriver || /HeadlessChrome|headless/i.test(navigator.userAgent))) {
    return false;
  }
  try {
    const canvas = document.createElement('canvas');
    return !!(
      window.WebGLRenderingContext &&
      (canvas.getContext('webgl') || canvas.getContext('experimental-webgl'))
    );
  } catch (e) {
    return false;
  }
}

