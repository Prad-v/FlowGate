import { useState, useEffect } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { agentTagApi, TagInfo } from '../services/api'

interface AgentTagManagerProps {
  gatewayId: string
  orgId: string
  onClose: () => void
}

export default function AgentTagManager({ gatewayId, orgId, onClose }: AgentTagManagerProps) {
  const queryClient = useQueryClient()
  const [newTag, setNewTag] = useState('')

  const { data: currentTags } = useQuery({
    queryKey: ['agent-tags', gatewayId, orgId],
    queryFn: () => agentTagApi.getTags(gatewayId, orgId),
  })

  const { data: allTags } = useQuery({
    queryKey: ['all-tags', orgId],
    queryFn: () => agentTagApi.getAllTags(orgId),
  })

  const addTagMutation = useMutation({
    mutationFn: (tag: string) => agentTagApi.addTag(gatewayId, orgId, tag),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['agent-tags', gatewayId] })
      queryClient.invalidateQueries({ queryKey: ['all-tags', orgId] })
      queryClient.invalidateQueries({ queryKey: ['agents', orgId] })
      setNewTag('')
    },
  })

  const removeTagMutation = useMutation({
    mutationFn: (tag: string) => agentTagApi.removeTag(gatewayId, orgId, tag),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['agent-tags', gatewayId] })
      queryClient.invalidateQueries({ queryKey: ['all-tags', orgId] })
      queryClient.invalidateQueries({ queryKey: ['agents', orgId] })
    },
  })

  const handleAddTag = () => {
    if (newTag.trim() && !currentTags?.includes(newTag.trim().toLowerCase())) {
      addTagMutation.mutate(newTag.trim())
    }
  }

  const handleRemoveTag = (tag: string) => {
    removeTagMutation.mutate(tag)
  }

  const suggestedTags = allTags
    ?.filter((tagInfo) => !currentTags?.includes(tagInfo.tag))
    .slice(0, 5) || []

  return (
    <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
      <div className="relative top-20 mx-auto p-5 border w-96 shadow-lg rounded-md bg-white">
        <div className="flex justify-between items-center mb-4">
          <h3 className="text-lg font-medium text-gray-900">Manage Tags</h3>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-500"
          >
            <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        <div className="space-y-4">
          {/* Current Tags */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Current Tags</label>
            <div className="flex flex-wrap gap-2">
              {currentTags && currentTags.length > 0 ? (
                currentTags.map((tag) => (
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
                <span className="text-sm text-gray-500">No tags</span>
              )}
            </div>
          </div>

          {/* Add Tag */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Add Tag</label>
            <div className="flex space-x-2">
              <input
                type="text"
                value={newTag}
                onChange={(e) => setNewTag(e.target.value)}
                onKeyPress={(e) => {
                  if (e.key === 'Enter') {
                    handleAddTag()
                  }
                }}
                className="flex-1 px-3 py-2 border border-gray-300 rounded-md shadow-sm text-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                placeholder="Enter tag name..."
              />
              <button
                onClick={handleAddTag}
                disabled={!newTag.trim() || addTagMutation.isPending}
                className="px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50"
              >
                Add
              </button>
            </div>
          </div>

          {/* Suggested Tags */}
          {suggestedTags.length > 0 && (
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Suggested Tags</label>
              <div className="flex flex-wrap gap-2">
                {suggestedTags.map((tagInfo) => (
                  <button
                    key={tagInfo.tag}
                    onClick={() => {
                      setNewTag(tagInfo.tag)
                      handleAddTag()
                    }}
                    className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-gray-100 text-gray-800 hover:bg-gray-200"
                  >
                    {tagInfo.tag} ({tagInfo.count})
                  </button>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

