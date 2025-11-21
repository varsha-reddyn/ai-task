import { useState, useEffect } from 'react'
import axios from 'axios'
import ReactJson from 'react-json-view'

// Configuration for API URL
// 1. Uses VITE_API_URL from .env if defined (e.g. http://16.112.64.187:8000)
// 2. Falls back to relative path '' in production (uses Docker/Nginx proxy)
// 3. Falls back to localhost:8000 in development
const API_BASE_URL = import.meta.env.VITE_API_URL || (import.meta.env.PROD ? '' : 'http://localhost:8000')

function App() {
  const [file, setFile] = useState(null)
  const [preview, setPreview] = useState(null)
  const [uploading, setUploading] = useState(false)
  const [uploadProgress, setUploadProgress] = useState(0)
  const [currentResult, setCurrentResult] = useState(null)
  const [records, setRecords] = useState([])
  const [selectedRecord, setSelectedRecord] = useState(null)
  const [showJsonView, setShowJsonView] = useState(false)
  const [editingRecord, setEditingRecord] = useState(null)
  const [activeTab, setActiveTab] = useState('upload')

  useEffect(() => {
    fetchRecords()
  }, [])

  const fetchRecords = async () => {
    try {
      const response = await axios.get(`${API_BASE_URL}/records?t=${new Date().getTime()}`) 
      if (response.data && Array.isArray(response.data.records)) {
         setRecords(response.data.records)
      } else {
         console.error('Invalid records format:', response.data)
      }
    } catch (error) {
      console.error('Error fetching records:', error)
    }
  }

  const handleFileChange = (e) => {
    const selectedFile = e.target.files[0]
    if (selectedFile) {
      setFile(selectedFile)
      const reader = new FileReader()
      reader.onloadend = () => {
        setPreview(reader.result)
      }
      reader.readAsDataURL(selectedFile)
    }
  }

  const handleDragOver = (e) => {
    e.preventDefault()
  }

  const handleDrop = (e) => {
    e.preventDefault()
    const droppedFile = e.dataTransfer.files[0]
    if (droppedFile) {
      setFile(droppedFile)
      const reader = new FileReader()
      reader.onloadend = () => {
        setPreview(reader.result)
      }
      reader.readAsDataURL(droppedFile)
    }
  }

  const handleUpload = async () => {
    if (!file) {
      alert('Please select a file first')
      return
    }

    const formData = new FormData()
    formData.append('file', file)

    setUploading(true)
    setUploadProgress(0)

    try {
      const response = await axios.post(`${API_BASE_URL}/upload`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
        onUploadProgress: (progressEvent) => {
          const progress = Math.round((progressEvent.loaded * 100) / progressEvent.total)
          setUploadProgress(progress)
        },
      })

      const result = await axios.get(`${API_BASE_URL}/result/${response.data.task_id}`)
      setCurrentResult(result.data)
      await fetchRecords()
      setActiveTab('results')
    } catch (error) {
      console.error('Error uploading file:', error)
      const errorMessage = error.response?.data?.detail || error.message || 'Error uploading file. Please try again.'
      alert(errorMessage)
    } finally {
      setUploading(false)
      setUploadProgress(0)
    }
  }

  const handleDelete = async (recordId) => {
    if (!confirm('Are you sure you want to delete this record?')) {
      return
    }

    try {
      await axios.delete(`${API_BASE_URL}/records/${recordId}`)
      await fetchRecords()
      if (selectedRecord?.id === recordId) {
        setSelectedRecord(null)
      }
      if (currentResult?.record_id === recordId) {
        setCurrentResult(null)
      }
    } catch (error) {
      console.error('Error deleting record:', error)
      alert('Error deleting record')
    }
  }

  const handleEdit = (record) => {
    setEditingRecord({
      id: record.id,
      raw_json: JSON.parse(JSON.stringify(record.raw_json))
    })
  }

  const handleSaveEdit = async () => {
    if (!editingRecord) return

    try {
      await axios.put(`${API_BASE_URL}/records/${editingRecord.id}`, {
        raw_json: editingRecord.raw_json
      })
      await fetchRecords()
      setEditingRecord(null)
      if (selectedRecord?.id === editingRecord.id) {
        const updated = await axios.get(`${API_BASE_URL}/records/${editingRecord.id}`)
        setSelectedRecord(updated.data)
      }
    } catch (error) {
      console.error('Error updating record:', error)
      alert('Error updating record')
    }
  }

  const handleFieldChange = (index, field, value) => {
    const updated = { ...editingRecord }
    updated.raw_json.fields[index][field] = value
    setEditingRecord(updated)
  }

  const downloadJSON = (data, filename = 'extracted-data.json') => {
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = filename
    a.click()
    URL.revokeObjectURL(url)
  }

  const downloadCSV = (data, filename = 'extracted-data.csv') => {
    if (!data.fields || data.fields.length === 0) {
      alert('No data to download')
      return
    }

    const headers = 'Label,Value\n'
    const rows = data.fields.map(field => `"${field.label}","${field.value}"`).join('\n')
    const csv = headers + rows

    const blob = new Blob([csv], { type: 'text/csv' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = filename
    a.click()
    URL.revokeObjectURL(url)
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
      <div className="container mx-auto px-4 py-8">
        <h1 className="text-4xl font-bold text-center text-indigo-900 mb-8">
          Handwritten Form Extraction System
        </h1>

        <div className="mb-6">
          <div className="flex space-x-4 border-b border-indigo-200">
            <button
              onClick={() => setActiveTab('upload')}
              className={`px-6 py-3 font-semibold ${
                activeTab === 'upload'
                  ? 'border-b-4 border-indigo-600 text-indigo-600'
                  : 'text-gray-600 hover:text-indigo-600'
              }`}
            >
              Upload Form
            </button>
            <button
              onClick={() => setActiveTab('results')}
              className={`px-6 py-3 font-semibold ${
                activeTab === 'results'
                  ? 'border-b-4 border-indigo-600 text-indigo-600'
                  : 'text-gray-600 hover:text-indigo-600'
              }`}
            >
              All Records ({records.length})
            </button>
          </div>
        </div>

        {activeTab === 'upload' && (
          <div className="bg-white rounded-lg shadow-xl p-8 mb-8">
            <h2 className="text-2xl font-semibold text-gray-800 mb-6">Upload Handwritten Form</h2>
            
            <div
              onDragOver={handleDragOver}
              onDrop={handleDrop}
              className="border-4 border-dashed border-indigo-300 rounded-lg p-12 text-center hover:border-indigo-500 transition-colors cursor-pointer"
            >
              <input
                type="file"
                onChange={handleFileChange}
                accept=".png,.jpg,.jpeg,.pdf"
                className="hidden"
                id="file-upload"
              />
              <label htmlFor="file-upload" className="cursor-pointer">
                <div className="text-6xl mb-4">📄</div>
                <p className="text-xl text-gray-700 mb-2">
                  Drag and drop your file here or click to browse
                </p>
                <p className="text-sm text-gray-500">Supported formats: PNG, JPG, JPEG, PDF</p>
              </label>
            </div>

            {preview && (
              <div className="mt-6">
                <h3 className="text-lg font-semibold mb-3">Preview:</h3>
                <img src={preview} alt="Preview" className="max-w-md mx-auto rounded-lg shadow-md" />
              </div>
            )}

            {uploading && (
              <div className="mt-6">
                <div className="w-full bg-gray-200 rounded-full h-4">
                  <div
                    className="bg-indigo-600 h-4 rounded-full transition-all duration-300"
                    style={{ width: `${uploadProgress}%` }}
                  ></div>
                </div>
                <p className="text-center mt-2 text-gray-700">Uploading: {uploadProgress}%</p>
              </div>
            )}

            <button
              onClick={handleUpload}
              disabled={!file || uploading}
              className="mt-6 w-full bg-indigo-600 text-white py-3 px-6 rounded-lg font-semibold hover:bg-indigo-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors"
            >
              {uploading ? 'Processing...' : 'Upload & Extract'}
            </button>

            {currentResult && (
              <div className="mt-8 bg-gray-50 rounded-lg p-6">
                <div className="flex justify-between items-center mb-4">
                  <h3 className="text-xl font-semibold">Extraction Result</h3>
                  <div className="space-x-2">
                    <button
                      onClick={() => setShowJsonView(!showJsonView)}
                      className="px-4 py-2 bg-gray-600 text-white rounded hover:bg-gray-700"
                    >
                      {showJsonView ? 'Table View' : 'JSON View'}
                    </button>
                    <button
                      onClick={() => downloadJSON(currentResult.data)}
                      className="px-4 py-2 bg-green-600 text-white rounded hover:bg-green-700"
                    >
                      Download JSON
                    </button>
                    <button
                      onClick={() => downloadCSV(currentResult.data)}
                      className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
                    >
                      Download CSV
                    </button>
                  </div>
                </div>

                {showJsonView ? (
                  <ReactJson src={currentResult.data} theme="rjv-default" collapsed={false} />
                ) : (
                  <table className="w-full border-collapse border border-gray-300">
                    <thead>
                      <tr className="bg-indigo-100">
                        <th className="border border-gray-300 px-4 py-2 text-left">Label</th>
                        <th className="border border-gray-300 px-4 py-2 text-left">Value</th>
                      </tr>
                    </thead>
                    <tbody>
                      {currentResult.data.fields?.map((field, index) => (
                        <tr key={index} className="hover:bg-gray-100">
                          <td className="border border-gray-300 px-4 py-2 font-semibold">
                            {field.label}
                          </td>
                          <td className="border border-gray-300 px-4 py-2">{field.value}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                )}
              </div>
            )}
          </div>
        )}

        {activeTab === 'results' && (
          <div className="bg-white rounded-lg shadow-xl p-8">
            <h2 className="text-2xl font-semibold text-gray-800 mb-6">All Extracted Records</h2>

            {records.length === 0 ? (
              <p className="text-gray-600 text-center py-8">
                No records yet. Upload a form to get started!
              </p>
            ) : (
              <div className="space-y-4">
                {records.map((record) => (
                  <div
                    key={record.id}
                    className="border border-gray-300 rounded-lg p-6 hover:shadow-lg transition-shadow"
                  >
                    <div className="flex justify-between items-start mb-4">
                      <div>
                        <h3 className="text-lg font-semibold text-indigo-900">
                          Record #{record.id}
                        </h3>
                        <p className="text-sm text-gray-500">
                          Created: {new Date(record.created_at).toLocaleString()}
                        </p>
                        {record.updated_at !== record.created_at && (
                          <p className="text-sm text-gray-500">
                            Updated: {new Date(record.updated_at).toLocaleString()}
                          </p>
                        )}
                      </div>
                      <div className="space-x-2">
                        <button
                          onClick={() => handleEdit(record)}
                          className="px-4 py-2 bg-yellow-500 text-white rounded hover:bg-yellow-600"
                        >
                          Edit
                        </button>
                        <button
                          onClick={() => downloadJSON(record.raw_json, `record-${record.id}.json`)}
                          className="px-4 py-2 bg-green-600 text-white rounded hover:bg-green-700"
                        >
                          JSON
                        </button>
                        <button
                          onClick={() => downloadCSV(record.raw_json, `record-${record.id}.csv`)}
                          className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
                        >
                          CSV
                        </button>
                        <button
                          onClick={() => handleDelete(record.id)}
                          className="px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700"
                        >
                          Delete
                        </button>
                      </div>
                    </div>

                    {editingRecord?.id === record.id ? (
                      <div className="bg-yellow-50 p-4 rounded">
                        <h4 className="font-semibold mb-3">Editing Record</h4>
                        <table className="w-full border-collapse border border-gray-300 mb-4">
                          <thead>
                            <tr className="bg-yellow-100">
                              <th className="border border-gray-300 px-4 py-2">Label</th>
                              <th className="border border-gray-300 px-4 py-2">Value</th>
                            </tr>
                          </thead>
                          <tbody>
                            {editingRecord.raw_json.fields?.map((field, index) => (
                              <tr key={index}>
                                <td className="border border-gray-300 px-2 py-2">
                                  <input
                                    type="text"
                                    value={field.label}
                                    onChange={(e) =>
                                      handleFieldChange(index, 'label', e.target.value)
                                    }
                                    className="w-full px-2 py-1 border border-gray-300 rounded"
                                  />
                                </td>
                                <td className="border border-gray-300 px-2 py-2">
                                  <input
                                    type="text"
                                    value={field.value}
                                    onChange={(e) =>
                                      handleFieldChange(index, 'value', e.target.value)
                                    }
                                    className="w-full px-2 py-1 border border-gray-300 rounded"
                                  />
                                </td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                        <div className="space-x-2">
                          <button
                            onClick={handleSaveEdit}
                            className="px-4 py-2 bg-green-600 text-white rounded hover:bg-green-700"
                          >
                            Save Changes
                          </button>
                          <button
                            onClick={() => setEditingRecord(null)}
                            className="px-4 py-2 bg-gray-600 text-white rounded hover:bg-gray-700"
                          >
                            Cancel
                          </button>
                        </div>
                      </div>
                    ) : (
                      <table className="w-full border-collapse border border-gray-300">
                        <thead>
                          <tr className="bg-gray-100">
                            <th className="border border-gray-300 px-4 py-2 text-left">Label</th>
                            <th className="border border-gray-300 px-4 py-2 text-left">Value</th>
                          </tr>
                        </thead>
                        <tbody>
                          {record.raw_json.fields?.map((field, index) => (
                            <tr key={index} className="hover:bg-gray-50">
                              <td className="border border-gray-300 px-4 py-2 font-semibold">
                                {field.label}
                              </td>
                              <td className="border border-gray-300 px-4 py-2">{field.value}</td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  )
}

export default App
