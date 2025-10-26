import { create } from 'zustand';

const useThemeStore = create((set) => ({
  darkMode: localStorage.getItem('darkMode') === 'true' || false,

  toggleDarkMode: () => set((state) => {
    const newDarkMode = !state.darkMode;
    localStorage.setItem('darkMode', newDarkMode.toString());

    // Apply or remove dark class from document element
    if (newDarkMode) {
      document.documentElement.classList.add('dark');
    } else {
      document.documentElement.classList.remove('dark');
    }

    return { darkMode: newDarkMode };
  }),

  initializeDarkMode: () => {
    const darkMode = localStorage.getItem('darkMode') === 'true';
    if (darkMode) {
      document.documentElement.classList.add('dark');
    } else {
      document.documentElement.classList.remove('dark');
    }
    set({ darkMode });
  },
}));

export default useThemeStore;
