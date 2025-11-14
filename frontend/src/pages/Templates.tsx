import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { templateApi, Template, TemplateCreate } from '../services/api'
import { Link } from 'react-router-dom'

export default function Templates() {
  const [showCreateForm, setShowCreateForm] = useState(false)
  const queryClient = useQueryClient()

  const { data: templates, isLoading } = useQuery({
    queryKey: ['templates'],
    queryFn: templateApi.list,
  })

  const createMutation = useMutation({
    mutationFn: templateApi.create,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['templates'] })
      setShowCreateForm(false)
    },
  })

  const deleteMutation = useMutation({
    mutationFn: templateApi.delete,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['templates'] })
    },
  })

  const handleCreate = (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault()
    const formData = new FormData(e.currentTarget)
    const data: TemplateCreate = {
      name: formData.get('name') as string,
      description: formData.get('description') as string || undefined,
      template_type: formData.get('template_type') as TemplateCreate['template_type'],
      config_yaml: formData.get('config_yaml') as string,
      change_summary: formData.get('change_summary') as string || undefined,
    }
    createMutation.mutate(data)
  }

  if (isLoading) {
    return <div className="px-4 py-6">Loading...</div>
  }

  return (
    <div className="px-4 py-6 sm:px-0">
      <div className="mb-8 flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Templates</h1>
          <p className="mt-2 text-sm text-gray-600">
            Manage your OTel collector configuration templates
          </p>
        </div>
        <button
          onClick={() => setShowCreateForm(!showCreateForm)}
          className="bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700"
        >
          {showCreateForm ? 'Cancel' : 'Create Template'}
        </button>
      </div>

      {showCreateForm && (
        <div className="mb-8 bg-white shadow rounded-lg p-6">
          <h2 className="text-xl font-semibold mb-4">Create New Template</h2>
          <form onSubmit={handleCreate} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700">Name</label>
              <input
                type="text"
                name="name"
                required
                className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700">Description</label>
              <textarea
                name="description"
                rows={2}
                className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700">Type</label>
              <select
                name="template_type"
                required
                className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
              >
                <option value="metric">Metric</option>
                <option value="log">Log</option>
                <option value="trace">Trace</option>
                <option value="routing">Routing</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700">Config YAML</label>
              <textarea
                name="config_yaml"
                required
                rows={10}
                className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 font-mono text-sm"
                placeholder="receivers:&#10;  otlp:&#10;    protocols:&#10;      grpc:&#10;        endpoint: 0.0.0.0:4317"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700">Change Summary</label>
              <input
                type="text"
                name="change_summary"
                className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
              />
            </div>
            <button
              type="submit"
              disabled={createMutation.isPending}
              className="bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700 disabled:opacity-50"
            >
              {createMutation.isPending ? 'Creating...' : 'Create Template'}
            </button>
          </form>
        </div>
      )}

      <div className="bg-white shadow overflow-hidden sm:rounded-md">
        <ul className="divide-y divide-gray-200">
          {templates?.map((template) => (
            <li key={template.id}>
              <div className="px-4 py-4 sm:px-6">
                <div className="flex items-center justify-between">
                  <div className="flex items-center">
                    <p className="text-sm font-medium text-blue-600 truncate">
                      {template.name}
                    </p>
                    <span className="ml-2 px-2 inline-flex text-xs leading-5 font-semibold rounded-full bg-gray-100 text-gray-800">
                      {template.template_type}
                    </span>
                    {template.is_active ? (
                      <span className="ml-2 px-2 inline-flex text-xs leading-5 font-semibold rounded-full bg-green-100 text-green-800">
                        Active
                      </span>
                    ) : (
                      <span className="ml-2 px-2 inline-flex text-xs leading-5 font-semibold rounded-full bg-gray-100 text-gray-800">
                        Inactive
                      </span>
                    )}
                  </div>
                  <div className="flex space-x-2">
                    <Link
                      to={`/templates/${template.id}`}
                      className="text-blue-600 hover:text-blue-800 text-sm"
                    >
                      View
                    </Link>
                    <button
                      onClick={() => deleteMutation.mutate(template.id)}
                      className="text-red-600 hover:text-red-800 text-sm"
                    >
                      Delete
                    </button>
                  </div>
                </div>
                {template.description && (
                  <p className="mt-2 text-sm text-gray-500">{template.description}</p>
                )}
                <div className="mt-2 sm:flex sm:justify-between">
                  <div className="sm:flex">
                    <p className="flex items-center text-sm text-gray-500">
                      Version {template.current_version}
                    </p>
                  </div>
                  <div className="mt-2 flex items-center text-sm text-gray-500 sm:mt-0">
                    Updated {new Date(template.updated_at).toLocaleDateString()}
                  </div>
                </div>
              </div>
            </li>
          ))}
        </ul>
        {templates?.length === 0 && (
          <div className="px-4 py-8 text-center text-gray-500">
            No templates found. Create your first template to get started.
          </div>
        )}
      </div>
    </div>
  )
}
