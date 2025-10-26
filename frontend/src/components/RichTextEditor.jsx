import { useEffect, useState } from 'react';
import { useEditor, EditorContent } from '@tiptap/react';
import StarterKit from '@tiptap/starter-kit';
import Placeholder from '@tiptap/extension-placeholder';
import { lettersAPI } from '../services/api';

// Helper function to convert plain text to HTML preserving line breaks
const textToHtml = (text) => {
  if (!text) return '';
  // Split by double line breaks for paragraphs, single line breaks for <br>
  const paragraphs = text.split('\n\n');
  return paragraphs.map(p => {
    const lines = p.split('\n').filter(line => line.trim());
    if (lines.length === 0) return '';
    return `<p>${lines.join('<br>')}</p>`;
  }).join('');
};

// Helper function to convert HTML back to plain text preserving structure
const htmlToText = (html) => {
  if (!html) return '';
  // Create a temporary div to parse HTML
  const temp = document.createElement('div');
  temp.innerHTML = html;

  // Get text content but preserve paragraph breaks
  const paragraphs = Array.from(temp.querySelectorAll('p, h1, h2, h3, h4, h5, h6, li'));
  if (paragraphs.length === 0) {
    return temp.textContent || '';
  }

  const result = [];
  paragraphs.forEach((p, index) => {
    // Handle line breaks within paragraphs
    const text = p.innerHTML
      .split('<br>')
      .map(line => {
        const div = document.createElement('div');
        div.innerHTML = line;
        return (div.textContent || '').trim();
      })
      .filter(line => line.length > 0)
      .join('\n');

    if (text.trim()) {
      result.push(text);
    }
  });

  return result.join('\n\n');
};

export default function RichTextEditor({ value, onChange, placeholder = 'Enter letter content...' }) {
  const [aiLoading, setAiLoading] = useState(false);
  const [aiType, setAiType] = useState(null);
  const [copied, setCopied] = useState(false);
  const [showCustomInput, setShowCustomInput] = useState(false);
  const [customPrompt, setCustomPrompt] = useState('');

  const editor = useEditor({
    extensions: [
      StarterKit,
      Placeholder.configure({
        placeholder,
      }),
    ],
    content: textToHtml(value || ''),
    onUpdate: ({ editor }) => {
      const html = editor.getHTML();
      const plainText = htmlToText(html);
      onChange(plainText);
    },
    editorProps: {
      attributes: {
        class: 'prose dark:prose-invert max-w-none focus:outline-none min-h-[300px] p-4 text-gray-900 dark:text-white',
        spellcheck: 'true',
      },
    },
  });

  // Update editor content when value prop changes
  useEffect(() => {
    if (editor && value) {
      const currentPlainText = htmlToText(editor.getHTML());
      if (value !== currentPlainText) {
        editor.commands.setContent(textToHtml(value));
      }
    }
  }, [value, editor]);

  const handleCopy = async () => {
    if (!editor) return;

    const html = editor.getHTML();
    const text = htmlToText(html);

    if (!text.trim()) {
      alert('Nothing to copy');
      return;
    }

    try {
      await navigator.clipboard.writeText(text);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch (error) {
      alert('Failed to copy to clipboard');
    }
  };

  const handleAIImprovement = async (type, prompt = null) => {
    if (!editor || aiLoading) return;

    const html = editor.getHTML();
    const text = htmlToText(html);

    if (!text.trim()) {
      alert('Please enter some text first');
      return;
    }

    setAiLoading(true);
    setAiType(type);

    try {
      const response = await lettersAPI.improveText(text, type, prompt);
      const improvedText = response.data.improved;
      editor.commands.setContent(textToHtml(improvedText));
      onChange(improvedText);

      // Reset custom input if it was used
      if (type === 'custom') {
        setShowCustomInput(false);
        setCustomPrompt('');
      }
    } catch (error) {
      alert('Failed to improve text: ' + (error.response?.data?.detail || error.message));
    } finally {
      setAiLoading(false);
      setAiType(null);
    }
  };

  const handleCustomImprovement = () => {
    if (!customPrompt.trim()) {
      alert('Please enter custom instructions');
      return;
    }
    handleAIImprovement('custom', customPrompt);
  };

  if (!editor) {
    return null;
  }

  return (
    <div className="border border-gray-300 dark:border-gray-600 rounded-md overflow-hidden bg-white dark:bg-gray-900">
      {/* Toolbar */}
      <div className="bg-gray-50 dark:bg-gray-800 border-b border-gray-300 dark:border-gray-600 p-2 flex flex-wrap gap-2">
        {/* Formatting Buttons */}
        <button
          type="button"
          onClick={() => editor.chain().focus().toggleBold().run()}
          disabled={!editor.can().chain().focus().toggleBold().run()}
          className={`px-3 py-1 text-sm font-bold rounded ${
            editor.isActive('bold')
              ? 'bg-blue-600 text-white'
              : 'bg-white dark:bg-gray-700 border border-gray-300 dark:border-gray-600 text-gray-900 dark:text-white hover:bg-gray-100 dark:hover:bg-gray-600'
          }`}
        >
          B
        </button>
        <button
          type="button"
          onClick={() => editor.chain().focus().toggleItalic().run()}
          disabled={!editor.can().chain().focus().toggleItalic().run()}
          className={`px-3 py-1 text-sm italic rounded ${
            editor.isActive('italic')
              ? 'bg-blue-600 text-white'
              : 'bg-white dark:bg-gray-700 border border-gray-300 dark:border-gray-600 text-gray-900 dark:text-white hover:bg-gray-100 dark:hover:bg-gray-600'
          }`}
        >
          I
        </button>

        <div className="hidden sm:block w-px bg-gray-300 dark:bg-gray-600 mx-1"></div>

        {/* Heading Buttons - Hidden on mobile */}
        <button
          type="button"
          onClick={() => editor.chain().focus().toggleHeading({ level: 1 }).run()}
          className={`hidden sm:inline-flex px-3 py-1 text-sm rounded ${
            editor.isActive('heading', { level: 1 })
              ? 'bg-blue-600 text-white'
              : 'bg-white dark:bg-gray-700 border border-gray-300 dark:border-gray-600 text-gray-900 dark:text-white hover:bg-gray-100 dark:hover:bg-gray-600'
          }`}
        >
          H1
        </button>
        <button
          type="button"
          onClick={() => editor.chain().focus().toggleHeading({ level: 2 }).run()}
          className={`hidden sm:inline-flex px-3 py-1 text-sm rounded ${
            editor.isActive('heading', { level: 2 })
              ? 'bg-blue-600 text-white'
              : 'bg-white dark:bg-gray-700 border border-gray-300 dark:border-gray-600 text-gray-900 dark:text-white hover:bg-gray-100 dark:hover:bg-gray-600'
          }`}
        >
          H2
        </button>

        <div className="hidden sm:block w-px bg-gray-300 dark:bg-gray-600 mx-1"></div>

        {/* List Buttons */}
        <button
          type="button"
          onClick={() => editor.chain().focus().toggleBulletList().run()}
          className={`px-3 py-1 text-sm rounded ${
            editor.isActive('bulletList')
              ? 'bg-blue-600 text-white'
              : 'bg-white dark:bg-gray-700 border border-gray-300 dark:border-gray-600 text-gray-900 dark:text-white hover:bg-gray-100 dark:hover:bg-gray-600'
          }`}
        >
          • List
        </button>
        <button
          type="button"
          onClick={() => editor.chain().focus().toggleOrderedList().run()}
          className={`px-3 py-1 text-sm rounded ${
            editor.isActive('orderedList')
              ? 'bg-blue-600 text-white'
              : 'bg-white dark:bg-gray-700 border border-gray-300 dark:border-gray-600 text-gray-900 dark:text-white hover:bg-gray-100 dark:hover:bg-gray-600'
          }`}
        >
          1. List
        </button>

        <div className="w-px bg-gray-300 dark:bg-gray-600 mx-1"></div>

        {/* Copy Button */}
        <button
          type="button"
          onClick={handleCopy}
          className={`px-3 py-1 text-sm rounded ${
            copied
              ? 'bg-green-600 text-white'
              : 'bg-white dark:bg-gray-700 border border-gray-300 dark:border-gray-600 text-gray-900 dark:text-white hover:bg-gray-100 dark:hover:bg-gray-600'
          }`}
        >
          {copied ? '✓ Copied' : '📋 Copy'}
        </button>

        <div className="flex-grow"></div>

        {/* AI Assistance Buttons */}
        <div className="flex flex-wrap gap-2 border-l border-gray-300 dark:border-gray-600 pl-2">
          <button
            type="button"
            onClick={() => handleAIImprovement('grammar')}
            disabled={aiLoading}
            className="px-3 py-1 text-sm bg-purple-600 text-white rounded hover:bg-purple-700 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {aiLoading && aiType === 'grammar' ? '...' : '✓ Fix Grammar'}
          </button>
          <button
            type="button"
            onClick={() => handleAIImprovement('persuasive')}
            disabled={aiLoading}
            className="hidden sm:inline-flex px-3 py-1 text-sm bg-purple-600 text-white rounded hover:bg-purple-700 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {aiLoading && aiType === 'persuasive' ? '...' : '💪 More Persuasive'}
          </button>
          <button
            type="button"
            onClick={() => handleAIImprovement('shorten')}
            disabled={aiLoading}
            className="hidden sm:inline-flex px-3 py-1 text-sm bg-purple-600 text-white rounded hover:bg-purple-700 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {aiLoading && aiType === 'shorten' ? '...' : '📉 Shorten'}
          </button>
          <button
            type="button"
            onClick={() => handleAIImprovement('expand')}
            disabled={aiLoading}
            className="hidden sm:inline-flex px-3 py-1 text-sm bg-purple-600 text-white rounded hover:bg-purple-700 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {aiLoading && aiType === 'expand' ? '...' : '📈 Expand'}
          </button>
          <button
            type="button"
            onClick={() => setShowCustomInput(!showCustomInput)}
            disabled={aiLoading}
            className={`px-3 py-1 text-sm rounded hover:bg-purple-700 disabled:opacity-50 disabled:cursor-not-allowed ${
              showCustomInput ? 'bg-purple-700 text-white' : 'bg-purple-600 text-white'
            }`}
          >
            ✨ Custom
          </button>
        </div>
      </div>

      {/* Custom Input Section */}
      {showCustomInput && (
        <div className="bg-purple-50 dark:bg-purple-900/30 border-b border-purple-200 dark:border-purple-700 p-3 space-y-2">
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
            Custom Instructions:
          </label>
          <textarea
            value={customPrompt}
            onChange={(e) => setCustomPrompt(e.target.value)}
            placeholder="e.g., Make this more formal, Add more emotional appeal, Focus on economic impacts..."
            className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-900 text-gray-900 dark:text-white placeholder-gray-400 dark:placeholder-gray-500 rounded-md focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent"
            rows={2}
            disabled={aiLoading}
          />
          <div className="flex gap-2">
            <button
              type="button"
              onClick={handleCustomImprovement}
              disabled={aiLoading || !customPrompt.trim()}
              className="px-4 py-1.5 text-sm bg-purple-600 text-white rounded hover:bg-purple-700 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {aiLoading && aiType === 'custom' ? 'Improving...' : 'Apply Custom'}
            </button>
            <button
              type="button"
              onClick={() => {
                setShowCustomInput(false);
                setCustomPrompt('');
              }}
              disabled={aiLoading}
              className="px-4 py-1.5 text-sm bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-300 rounded hover:bg-gray-300 dark:hover:bg-gray-600 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Cancel
            </button>
          </div>
        </div>
      )}

      {/* Editor Content */}
      <EditorContent editor={editor} />

      {/* Word Count */}
      <div className="bg-gray-50 dark:bg-gray-800 border-t border-gray-300 dark:border-gray-600 px-4 py-2 text-xs text-gray-600 dark:text-gray-400">
        {editor.storage.characterCount?.characters() || editor.getText().split(/\s+/).filter(w => w).length} words
      </div>
    </div>
  );
}
