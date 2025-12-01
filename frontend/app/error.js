'use client';

import { useEffect } from 'react';
import styles from './error.module.css';

export default function Error({ error, reset }) {
  useEffect(() => {
    if (error) {
      // Surface error to console for visibility in logs
      console.error('Unhandled UI error:', error);
    }
  }, [error]);

  return (
    <div className={styles.wrapper}>
      <div className={styles.card}>
        <p className={styles.kicker}>Something went wrong</p>
        <h1>We hit a snag</h1>
        <p className={styles.message}>
          {error?.message || 'An unexpected error occurred. Please try again.'}
        </p>
        <div className={styles.actions}>
          <button className={styles.primary} type="button" onClick={reset}>
            Try again
          </button>
          <a className={styles.secondary} href="/">
            Back to home
          </a>
        </div>
      </div>
    </div>
  );
}
