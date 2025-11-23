import React, { useState, useEffect } from 'react'

interface ConfigField {
  key: string
  value: any
  type: 'string' | 'number' | 'boolean' | 'object' | 'array'
  required?: boolean
  description?: string
}

interface ComponentConfigFormProps {
  componentId: string
  componentType: string
  config: Record<string, any>
  defaultConfig?: Record<string, any>
  onChange: (config: Record<string, any>) => void
}

export default function ComponentConfigForm({
  componentId,
  componentType,
  config,
  defaultConfig = {},
  onChange,
}: ComponentConfigFormProps) {
  const [localConfig, setLocalConfig] = useState<Record<string, any>>(config || {})
  const [expandedFields, setExpandedFields] = useState<Set<string>>(new Set())

  useEffect(() => {
    setLocalConfig(config || {})
  }, [config])

  const flattenConfig = (obj: any, prefix = '', required = false, isDefault = true): ConfigField[] => {
    const fields: ConfigField[] = []
    
    if (!obj || typeof obj !== 'object') {
      return fields
    }
    
    for (const [key, value] of Object.entries(obj)) {
      const fullKey = prefix ? `${prefix}.${key}` : key
      
      if (value === null || value === undefined) {
        continue
      }
      
      if (typeof value === 'object' && !Array.isArray(value)) {
        if (Object.keys(value).length === 0) {
          // Empty object - treat as optional object field
          fields.push({
            key: fullKey,
            value: {},
            type: 'object',
            required: false,
            description: isDefault ? 'Suggested configuration' : undefined,
          })
        } else {
          // Nested object - add expandable section
          fields.push({
            key: fullKey,
            value: value,
            type: 'object',
            required: false, // Don't mark nested objects as required
            description: isDefault ? 'Suggested configuration' : undefined,
          })
          // Recursively add nested fields
          fields.push(...flattenConfig(value, fullKey, false, isDefault))
        }
      } else if (Array.isArray(value)) {
        fields.push({
          key: fullKey,
          value: value,
          type: 'array',
          required: false,
          description: isDefault ? 'Suggested configuration' : undefined,
        })
      } else {
        fields.push({
          key: fullKey,
          value: value,
          type: typeof value as 'string' | 'number' | 'boolean',
          required: false, // Mark as suggested, not required
          description: isDefault ? 'Suggested configuration' : undefined,
        })
      }
    }
    
    return fields
  }

  const updateConfig = (key: string, value: any) => {
    const newConfig = { ...localConfig }
    const keys = key.split('.')
    let current: any = newConfig
    
    for (let i = 0; i < keys.length - 1; i++) {
      if (!current[keys[i]]) {
        current[keys[i]] = {}
      }
      current = current[keys[i]]
    }
    
    current[keys[keys.length - 1]] = value
    setLocalConfig(newConfig)
    onChange(newConfig)
  }

  const getValue = (key: string): any => {
    const keys = key.split('.')
    let current: any = localConfig
    for (const k of keys) {
      if (current === null || current === undefined) return undefined
      current = current[k]
    }
    return current
  }

  const setValue = (key: string, value: any) => {
    if (value === '') {
      // Remove empty values
      const newConfig = { ...localConfig }
      const keys = key.split('.')
      let current: any = newConfig
      
      for (let i = 0; i < keys.length - 1; i++) {
        if (!current[keys[i]]) return
        current = current[keys[i]]
      }
      
      delete current[keys[keys.length - 1]]
      setLocalConfig(newConfig)
      onChange(newConfig)
    } else {
      updateConfig(key, value)
    }
  }

  const addFieldToObject = (objectKey: string, fieldName: string, fieldType: 'string' | 'number' | 'boolean' | 'object' = 'string') => {
    const currentValue = getValue(objectKey) || {}
    const newValue = { ...currentValue }
    
    // Special handling for known object fields
    const objectFields = ['tls', 'cors', 'auth', 'keepalive', 'protocols']
    if (objectFields.includes(fieldName.toLowerCase())) {
      newValue[fieldName] = {}
    } else if (fieldType === 'number') {
      newValue[fieldName] = 0
    } else if (fieldType === 'boolean') {
      newValue[fieldName] = false
    } else if (fieldType === 'object') {
      newValue[fieldName] = {}
    } else {
      newValue[fieldName] = ''
    }
    
    updateConfig(objectKey, newValue)
    
    // Auto-expand the object to show the new field
    const newExpanded = new Set(expandedFields)
    newExpanded.add(objectKey)
    // Also expand the new field if it's an object
    if (objectFields.includes(fieldName.toLowerCase()) || fieldType === 'object') {
      newExpanded.add(`${objectKey}.${fieldName}`)
    }
    setExpandedFields(newExpanded)
  }

  const renderField = (field: ConfigField) => {
    const value = getValue(field.key)
    const isExpanded = expandedFields.has(field.key)
    const isNested = field.key.includes('.')

    if (field.type === 'object') {
      // Object field - show as expandable section (both top-level and nested)
      const currentValue = value || field.value || {}
      const hasChildren = Object.keys(currentValue).length > 0
      const isEmpty = Object.keys(currentValue).length === 0
      
      return (
        <div key={field.key} className="mb-4">
          <button
            type="button"
            onClick={() => {
              const newExpanded = new Set(expandedFields)
              if (newExpanded.has(field.key)) {
                newExpanded.delete(field.key)
              } else {
                newExpanded.add(field.key)
              }
              setExpandedFields(newExpanded)
            }}
            className="flex items-center justify-between w-full px-3 py-2 bg-gray-50 border border-gray-300 rounded-md hover:bg-gray-100"
          >
            <span className="text-sm font-medium text-gray-700">
              {field.key.split('.').pop()} {field.required && <span className="text-red-500">*</span>}
              {isEmpty && <span className="ml-2 text-xs text-gray-400">(empty)</span>}
            </span>
            <span>{isExpanded ? '▼' : '▶'}</span>
          </button>
          {isExpanded && (
            <div className="mt-2 ml-4 pl-4 border-l-2 border-gray-200">
              {hasChildren ? (
                Object.entries(currentValue).map(([k, v]) => {
                  const nestedField: ConfigField = {
                    key: `${field.key}.${k}`,
                    value: v,
                    type: typeof v === 'object' && v !== null ? (Array.isArray(v) ? 'array' : 'object') : (typeof v as any),
                    required: false,
                  }
                  return renderField(nestedField)
                })
              ) : (
                <div className="text-xs text-gray-500 italic mb-2">No fields configured</div>
              )}
              {/* Quick Add Buttons for OTLP receiver */}
              {(field.key === 'protocols.grpc' || field.key === 'protocols.http') && (
                <div className="mt-2 mb-2 flex flex-wrap gap-2">
                  <button
                    type="button"
                    onClick={() => addFieldToObject(field.key, 'endpoint')}
                    className="text-xs px-2 py-1 bg-blue-50 text-blue-700 border border-blue-200 rounded hover:bg-blue-100"
                  >
                    + endpoint
                  </button>
                  {(field.key === 'protocols.grpc' || field.key === 'protocols.http') && (
                    <>
                      <button
                        type="button"
                        onClick={() => addFieldToObject(field.key, 'tls', 'object')}
                        className="text-xs px-2 py-1 bg-blue-50 text-blue-700 border border-blue-200 rounded hover:bg-blue-100"
                      >
                        + tls
                      </button>
                      {field.key === 'protocols.grpc' && (
                        <>
                          <button
                            type="button"
                            onClick={() => addFieldToObject(field.key, 'auth', 'object')}
                            className="text-xs px-2 py-1 bg-blue-50 text-blue-700 border border-blue-200 rounded hover:bg-blue-100"
                          >
                            + auth
                          </button>
                          <button
                            type="button"
                            onClick={() => addFieldToObject(field.key, 'max_recv_msg_size_mib', 'number')}
                            className="text-xs px-2 py-1 bg-blue-50 text-blue-700 border border-blue-200 rounded hover:bg-blue-100"
                          >
                            + max_recv_msg_size_mib
                          </button>
                        </>
                      )}
                      {field.key === 'protocols.http' && (
                        <>
                          <button
                            type="button"
                            onClick={() => addFieldToObject(field.key, 'cors', 'object')}
                            className="text-xs px-2 py-1 bg-blue-50 text-blue-700 border border-blue-200 rounded hover:bg-blue-100"
                          >
                            + cors
                          </button>
                          <button
                            type="button"
                            onClick={() => addFieldToObject(field.key, 'max_request_body_size', 'number')}
                            className="text-xs px-2 py-1 bg-blue-50 text-blue-700 border border-blue-200 rounded hover:bg-blue-100"
                          >
                            + max_request_body_size
                          </button>
                        </>
                      )}
                    </>
                  )}
                </div>
              )}
              {/* Add Field Button */}
              <div className="mt-2">
                <button
                  type="button"
                  onClick={() => {
                    const fieldName = prompt('Enter field name:')
                    if (fieldName && /^[a-zA-Z_][a-zA-Z0-9_]*$/.test(fieldName)) {
                      addFieldToObject(field.key, fieldName)
                    } else if (fieldName) {
                      alert('Field name must start with a letter or underscore and contain only letters, numbers, and underscores')
                    }
                  }}
                  className="text-xs text-blue-600 hover:text-blue-800"
                >
                  + Add Custom Field
                </button>
              </div>
            </div>
          )}
        </div>
      )
    }

    if (isNested && !isExpanded) {
      // Check if all parents in the path are expanded
      const keyParts = field.key.split('.')
      for (let i = 1; i < keyParts.length; i++) {
        const parentKey = keyParts.slice(0, i).join('.')
        if (!expandedFields.has(parentKey)) {
          return null
        }
      }
    }

    return (
      <div key={field.key} className="mb-3">
        <label className="block text-sm font-medium text-gray-700 mb-1">
          {field.key.split('.').pop()}
          {field.required && <span className="text-red-500 ml-1">*</span>}
        </label>
        
        {field.type === 'boolean' ? (
          <select
            value={value === true ? 'true' : value === false ? 'false' : ''}
            onChange={(e) => setValue(field.key, e.target.value === 'true')}
            className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm"
          >
            <option value="">Not set</option>
            <option value="true">True</option>
            <option value="false">False</option>
          </select>
        ) : field.type === 'number' ? (
          <input
            type="number"
            value={value ?? ''}
            onChange={(e) => setValue(field.key, e.target.value ? Number(e.target.value) : undefined)}
            className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm"
            placeholder={field.required ? 'Required' : 'Optional'}
          />
        ) : field.type === 'array' ? (
          <textarea
            value={Array.isArray(value) ? JSON.stringify(value, null, 2) : ''}
            onChange={(e) => {
              try {
                const parsed = JSON.parse(e.target.value)
                if (Array.isArray(parsed)) {
                  setValue(field.key, parsed)
                }
              } catch {
                // Invalid JSON, ignore
              }
            }}
            rows={4}
            className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm font-mono"
            placeholder='["item1", "item2"]'
          />
        ) : field.type === 'object' ? (
          <textarea
            value={typeof value === 'object' ? JSON.stringify(value, null, 2) : ''}
            onChange={(e) => {
              try {
                const parsed = JSON.parse(e.target.value)
                if (typeof parsed === 'object' && !Array.isArray(parsed)) {
                  setValue(field.key, parsed)
                }
              } catch {
                // Invalid JSON, ignore
              }
            }}
            rows={4}
            className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm font-mono"
            placeholder='{"key": "value"}'
          />
        ) : (
          <input
            type="text"
            value={value ?? ''}
            onChange={(e) => setValue(field.key, e.target.value || undefined)}
            className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm"
            placeholder={getFieldHint(field.key) || (field.required ? 'Required' : 'Optional')}
          />
        )}
        
        {getFieldHint(field.key) && (
          <p className="mt-1 text-xs text-gray-500">{getFieldHint(field.key)}</p>
        )}
        {field.description && (
          <p className="mt-1 text-xs text-gray-500 italic">{field.description}</p>
        )}
        {!field.required && !field.description && !getFieldHint(field.key) && (
          <p className="mt-1 text-xs text-gray-400 italic">Optional</p>
        )}
      </div>
    )
  }

  // Auto-expand top-level fields by default
  useEffect(() => {
    const topLevelFields = Object.keys(defaultConfig)
    if (topLevelFields.length > 0) {
      const newExpanded = new Set(expandedFields)
      topLevelFields.forEach((key) => {
        newExpanded.add(key)
      })
      setExpandedFields(newExpanded)
    }
  }, [defaultConfig])

  const allFields = flattenConfig(defaultConfig)
  const topLevelFields = allFields.filter((f) => !f.key.includes('.'))
  const hasConfig = Object.keys(localConfig).length > 0

  // Get OTLP-specific field hints
  const getFieldHint = (fieldKey: string): string | undefined => {
    const key = fieldKey.toLowerCase()
    if (key.includes('endpoint')) {
      return 'e.g., 0.0.0.0:4317 (gRPC) or 0.0.0.0:4318 (HTTP)'
    }
    if (key.includes('tls') || key.includes('cert') || key.includes('key')) {
      return 'Path to TLS certificate/key file'
    }
    if (key.includes('auth') || key.includes('authenticator')) {
      return 'Name of the authentication extension to use'
    }
    if (key.includes('max_recv_msg_size')) {
      return 'Maximum message size in MiB'
    }
    if (key.includes('cors')) {
      return 'CORS configuration for HTTP server'
    }
    return undefined
  }

  return (
    <div className="space-y-4">
      <div className="text-sm text-gray-600 mb-4">
        Configure <span className="font-semibold">{componentId}</span> ({componentType})
      </div>
      
      {!hasConfig && Object.keys(defaultConfig).length === 0 && (
        <div className="text-sm text-gray-500 italic">No configuration required for this component.</div>
      )}
      
      {topLevelFields.map((field) => renderField(field))}
      
      {hasConfig && (
        <div className="mt-4 pt-4 border-t border-gray-200">
          <details className="text-sm">
            <summary className="cursor-pointer text-gray-600 hover:text-gray-900">
              Advanced: Edit Raw JSON
            </summary>
            <textarea
              value={JSON.stringify(localConfig, null, 2)}
              onChange={(e) => {
                try {
                  const parsed = JSON.parse(e.target.value)
                  setLocalConfig(parsed)
                  onChange(parsed)
                } catch {
                  // Invalid JSON, ignore
                }
              }}
              rows={10}
              className="w-full mt-2 px-3 py-2 border border-gray-300 rounded-md text-xs font-mono"
            />
          </details>
        </div>
      )}
    </div>
  )
}

