import { useState } from 'react'
import { TagInfo } from '../services/api'

interface TagSelectorProps {
  selectedTags: string[]
  onTagsChange: (tags: string[]) => void
  allTags?: TagInfo[]
  showAllOption?: boolean
}

export default function TagSelector({
  selectedTags,
  onTagsChange,
  allTags = [],
  showAllOption = true,
}: TagSelectorProps) {
  const [isOpen, setIsOpen] = useState(false)
  const [searchTerm, setSearchTerm] = useState('')

  const filteredTags = allTags.filter((tagInfo) =>
    tagInfo.tag.toLowerCase().includes(searchTerm.toLowerCase())
  )

  const handleToggleTag = (tag: string) => {
    if (tag === '__all__') {
      onTagsChange([])
    } else if (selectedTags.includes(tag)) {
      onTagsChange(selectedTags.filter((t) => t !== tag))
    } else {
      onTagsChange([...selectedTags, tag])
    }
  }

  const handleRemoveTag = (tag: string) => {
    onTagsChange(selectedTags.filter((t) => t !== tag))
  }

  return (
    <div className="relative">
      <label className="block text-sm font-medium text-gray-700 mb-2">Target Tags</label>
      
      {/* Selected Tags Display */}
      <div className="flex flex-wrap gap-2 mb-2 min-h-[2.5rem] p-2 border border-gray-300 rounded-md bg-white">
        {selectedTags.length === 0 && showAllOption ? (
          <span className="text-sm text-gray-500">All Agents (default)</span>
        ) : selectedTags.length > 0 ? (
          selectedTags.map((tag) => (
            <span
              key={tag}
              className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800"
            >
              {tag}
              <button
                onClick={() => handleRemoveTag(tag)}
                className="ml-1 text-blue-600 hover:text-blue-800"
              >
                ×
              </button>
            </span>
          ))
        ) : (
          <span className="text-sm text-gray-500">No tags selected</span>
        )}
      </div>

      {/* Dropdown */}
      <div className="relative">
        <button
          type="button"
          onClick={() => setIsOpen(!isOpen)}
          className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm text-sm text-left bg-white focus:outline-none focus:ring-blue-500 focus:border-blue-500"
        >
          {selectedTags.length === 0 && showAllOption
            ? 'All Agents (default)'
            : `${selectedTags.length} tag${selectedTags.length !== 1 ? 's' : ''} selected`}
          <span className="float-right">▼</span>
        </button>

        {isOpen && (
          <div className="absolute z-10 mt-1 w-full bg-white shadow-lg max-h-60 rounded-md py-1 text-base ring-1 ring-black ring-opacity-5 overflow-auto focus:outline-none">
            {/* Search */}
            <div className="px-3 py-2 border-b">
              <input
                type="text"
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                placeholder="Search tags..."
                className="w-full px-2 py-1 border border-gray-300 rounded text-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
              />
            </div>

            {/* All Agents Option */}
            {showAllOption && (
              <div
                onClick={() => {
                  handleToggleTag('__all__')
                  setIsOpen(false)
                }}
                className={`px-4 py-2 cursor-pointer hover:bg-gray-100 ${
                  selectedTags.length === 0 ? 'bg-blue-50' : ''
                }`}
              >
                <div className="flex items-center">
                  <input
                    type="checkbox"
                    checked={selectedTags.length === 0}
                    onChange={() => {}}
                    className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                  />
                  <span className="ml-2 text-sm text-gray-900">All Agents (default)</span>
                </div>
              </div>
            )}

            {/* Tag Options */}
            {filteredTags.map((tagInfo) => (
              <div
                key={tagInfo.tag}
                onClick={() => handleToggleTag(tagInfo.tag)}
                className={`px-4 py-2 cursor-pointer hover:bg-gray-100 ${
                  selectedTags.includes(tagInfo.tag) ? 'bg-blue-50' : ''
                }`}
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center">
                    <input
                      type="checkbox"
                      checked={selectedTags.includes(tagInfo.tag)}
                      onChange={() => {}}
                      className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                    />
                    <span className="ml-2 text-sm text-gray-900">{tagInfo.tag}</span>
                  </div>
                  <span className="text-xs text-gray-500">({tagInfo.count})</span>
                </div>
              </div>
            ))}

            {filteredTags.length === 0 && (
              <div className="px-4 py-2 text-sm text-gray-500">No tags found</div>
            )}
          </div>
        )}
      </div>

      {selectedTags.length > 0 && (
        <p className="mt-1 text-xs text-gray-500">
          {selectedTags.length} tag{selectedTags.length !== 1 ? 's' : ''} selected. Only agents with these tags will receive the config.
        </p>
      )}
    </div>
  )
}

