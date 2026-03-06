export const throttle = <U, T extends (...args: any[]) => U>(callback: T, delay: number) => {
    let lastCall: number | null = null;

    return (...args: Parameters<T>) => {
        const now = Date.now();
        if (lastCall === null || now - lastCall >= delay) {
            lastCall = now;
            return callback(...args);
        }
    };
}

export const debounce = <U, T extends (...args: any[]) => U>(callback: T, delay: number) => {
    let timeoutId: ReturnType<typeof setTimeout> | null = null;

    return (...args: Parameters<T>) => {
        const later = () => {
            timeoutId = null;
            return callback(...args);
        };

        if (timeoutId !== null) {
            clearTimeout(timeoutId);
        }

        timeoutId = setTimeout(later, delay);
    };
}
