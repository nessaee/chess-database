/**
 * Utility function to conditionally join CSS class names together
 * @param  {...string} classes - Class names to be joined
 * @returns {string} - Joined class names with falsy values filtered out
 */
export function classNames(...classes) {
  return classes.filter(Boolean).join(' ');
}
