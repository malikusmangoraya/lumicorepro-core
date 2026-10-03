/**
 * CommandPalette - Spotlight-style Quick Actions
 * ================================================
 * Cmd+K style command palette for quick navigation and actions.
 * 
 * Features:
 * - Fuzzy search across all commands
 * - Keyboard navigation (arrows, enter, esc)
 * - Recent commands history
 * - Grouped commands by category
 * - Quick AI actions
 * - Theme switching
 */

import React, { useState, useEffect, useRef, useMemo } from 'react';
import { createPortal } from 'react-dom';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Search,
  Sparkles,
  Code,
  Settings,
  Moon,
  Sun,
  FileText,
  Zap,
  Home,
  LogOut,
  User,
  ChevronRight,
} from 'lucide-react';
import PropTypes from 'prop-types';

const CommandPalette = ({ isOpen, onClose, onExecute }) => {
  const [query, setQuery] = useState('');
  const [selectedIndex, setSelectedIndex] = useState(0);
  const [recentCommands, setRecentCommands] = useState([]);
  const inputRef = useRef(null);
  const listRef = useRef(null);

  // All available commands
  const commands = useMemo(
    () => [
      // Navigation
      {
        id: 'nav-home',
        label: 'Go to Home',
        icon: Home,
        category: 'Navigation',
        action: () => (window.location.href = '/'),
        keywords: ['home', 'dashboard', 'main'],
      },
      {
        id: 'nav-ai',
        label: 'Open AI Dashboard',
        icon: Sparkles,
        category: 'Navigation',
        action: () => (window.location.href = '/ai-dashboard'),
        keywords: ['ai', 'generate', 'dashboard'],
      },
      {
        id: 'nav-projects',
        label: 'View Projects',
        icon: FileText,
        category: 'Navigation',
        action: () => (window.location.href = '/projects'),
        keywords: ['projects', 'list'],
      },
      {
        id: 'nav-settings',
        label: 'Settings',
        icon: Settings,
        category: 'Navigation',
        action: () => (window.location.href = '/settings'),
        keywords: ['settings', 'preferences', 'config'],
      },

      // AI Actions
      {
        id: 'ai-generate',
        label: 'Generate New Website',
        icon: Sparkles,
        category: 'AI Actions',
        action: () => (window.location.href = '/generate'),
        keywords: ['generate', 'create', 'new', 'ai'],
      },
      {
        id: 'ai-chat',
        label: 'Open AI Chat',
        icon: Sparkles,
        category: 'AI Actions',
        action: () => (window.location.href = '/chat'),
        keywords: ['chat', 'ask', 'question'],
      },
      {
        id: 'ai-analyze',
        label: 'Analyze Code',
        icon: Code,
        category: 'AI Actions',
        action: () => (window.location.href = '/ai-dashboard'),
        keywords: ['analyze', 'code', 'review', 'security'],
      },

      // Theme
      {
        id: 'theme-light',
        label: 'Switch to Light Mode',
        icon: Sun,
        category: 'Appearance',
        action: () => document.documentElement.classList.remove('dark'),
        keywords: ['theme', 'light', 'mode'],
      },
      {
        id: 'theme-dark',
        label: 'Switch to Dark Mode',
        icon: Moon,
        category: 'Appearance',
        action: () => document.documentElement.classList.add('dark'),
        keywords: ['theme', 'dark', 'mode'],
      },

      // Account
      {
        id: 'account-profile',
        label: 'View Profile',
        icon: User,
        category: 'Account',
        action: () => (window.location.href = '/profile'),
        keywords: ['profile', 'account', 'user'],
      },
      {
        id: 'account-logout',
        label: 'Log Out',
        icon: LogOut,
        category: 'Account',
        action: () => {
          localStorage.removeItem('token');
          localStorage.removeItem('auth_token');
          sessionStorage.clear();
          window.location.href = '/login';
        },
        keywords: ['logout', 'signout', 'exit'],
      },
    ],
    []
  );

  // Fuzzy search
  const filteredCommands = useMemo(() => {
    if (!query) return commands;

    const lowerQuery = query.toLowerCase();
    return commands.filter((cmd) => {
      const labelMatch = cmd.label.toLowerCase().includes(lowerQuery);
      const keywordMatch = cmd.keywords.some((kw) => kw.includes(lowerQuery));
      return labelMatch || keywordMatch;
    });
  }, [query, commands]);

  // Group by category
  const groupedCommands = useMemo(() => {
    const groups = {};
    filteredCommands.forEach((cmd) => {
      if (!groups[cmd.category]) {
        groups[cmd.category] = [];
      }
      groups[cmd.category].push(cmd);
    });
    return groups;
  }, [filteredCommands]);

  // Keyboard navigation
  useEffect(() => {
    const handleKeyDown = (e) => {
      if (!isOpen) return;

      switch (e.key) {
        case 'ArrowDown':
          e.preventDefault();
          setSelectedIndex((prev) => Math.min(prev + 1, filteredCommands.length - 1));
          break;
        case 'ArrowUp':
          e.preventDefault();
          setSelectedIndex((prev) => Math.max(prev - 1, 0));
          break;
        case 'Enter':
          e.preventDefault();
          if (filteredCommands[selectedIndex]) {
            executeCommand(filteredCommands[selectedIndex]);
          }
          break;
        case 'Escape':
          e.preventDefault();
          onClose();
          break;
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, selectedIndex, filteredCommands]);

  // Focus input when opened
  useEffect(() => {
    if (isOpen && inputRef.current) {
      inputRef.current.focus();
      setQuery('');
      setSelectedIndex(0);
    }
  }, [isOpen]);

  // Scroll selected item into view
  useEffect(() => {
    if (listRef.current) {
      const selectedElement = listRef.current.children[selectedIndex];
      if (selectedElement && typeof selectedElement.scrollIntoView === 'function') {
        selectedElement.scrollIntoView({ block: 'nearest', behavior: 'smooth' });
      }
    }
  }, [selectedIndex]);

  const executeCommand = (command) => {
    // Execute command
    command.action();

    // Save to recent
    setRecentCommands((prev) => {
      const filtered = prev.filter((cmd) => cmd.id !== command.id);
      return [command, ...filtered].slice(0, 5);
    });

    // Callback
    onExecute?.(command);

    // Close
    onClose();
  };

  if (!isOpen) return null;

  return createPortal(
    <AnimatePresence>
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex items-start justify-center pt-[20vh]"
        onClick={onClose}
      >
        <motion.div
          initial={{ opacity: 0, scale: 0.95, y: -20 }}
          animate={{ opacity: 1, scale: 1, y: 0 }}
          exit={{ opacity: 0, scale: 0.95, y: -20 }}
          transition={{ type: 'spring', damping: 25, stiffness: 300 }}
          onClick={(e) => e.stopPropagation()}
          className="w-full max-w-2xl bg-white dark:bg-gray-900 rounded-2xl shadow-2xl overflow-hidden border border-gray-200 dark:border-gray-800"
        >
          {/* Search Input */}
          <div className="flex items-center px-4 py-4 border-b border-gray-200 dark:border-gray-800">
            <Search className="w-5 h-5 text-gray-400 mr-3" />
            <input
              ref={inputRef}
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Type a command or search..."
              className="flex-1 bg-transparent text-gray-900 dark:text-white placeholder-gray-400 outline-none text-lg"
            />
            <kbd className="px-2 py-1 text-xs bg-gray-100 dark:bg-gray-800 rounded border border-gray-300 dark:border-gray-700">
              ESC
            </kbd>
          </div>

          {/* Commands List */}
          <div
            ref={listRef}
            className="max-h-[400px] overflow-y-auto py-2 px-2"
          >
            {Object.keys(groupedCommands).length === 0 ? (
              <div className="py-12 text-center text-gray-500">
                No commands found
              </div>
            ) : (
              Object.entries(groupedCommands).map(([category, cmds]) => (
                <div key={category} className="mb-4">
                  <div className="px-3 py-1 text-xs font-semibold text-gray-500 uppercase tracking-wider">
                    {category}
                  </div>
                  {cmds.map((command, index) => {
                    const globalIndex = filteredCommands.indexOf(command);
                    const isSelected = globalIndex === selectedIndex;

                    return (
                      <motion.button
                        key={command.id}
                        onClick={() => executeCommand(command)}
                        className={`
                          w-full flex items-center gap-3 px-3 py-2.5 rounded-lg
                          transition-colors text-left
                          ${
                            isSelected
                              ? 'bg-primary text-white'
                              : 'text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-800'
                          }
                        `}
                        whileHover={{ x: 4 }}
                      >
                        <command.icon className="w-5 h-5 flex-shrink-0" />
                        <span className="flex-1 font-medium">{command.label}</span>
                        {isSelected && (
                          <ChevronRight className="w-4 h-4 flex-shrink-0" />
                        )}
                      </motion.button>
                    );
                  })}
                </div>
              ))
            )}
          </div>

          {/* Footer */}
          <div className="px-4 py-3 bg-gray-50 dark:bg-gray-800 border-t border-gray-200 dark:border-gray-700 flex items-center justify-between text-xs text-gray-500">
            <div className="flex items-center gap-4">
              <span className="flex items-center gap-1">
                <kbd className="px-1.5 py-0.5 bg-white dark:bg-gray-900 rounded border">↑</kbd>
                <kbd className="px-1.5 py-0.5 bg-white dark:bg-gray-900 rounded border">↓</kbd>
                navigate
              </span>
              <span className="flex items-center gap-1">
                <kbd className="px-1.5 py-0.5 bg-white dark:bg-gray-900 rounded border">↵</kbd>
                select
              </span>
            </div>
            <div>
              {filteredCommands.length} command{filteredCommands.length !== 1 && 's'}
            </div>
          </div>
        </motion.div>
      </motion.div>
    </AnimatePresence>,
    document.body
  );
};

CommandPalette.propTypes = {
  isOpen: PropTypes.bool.isRequired,
  onClose: PropTypes.func.isRequired,
  onExecute: PropTypes.func,
};

export default CommandPalette;
