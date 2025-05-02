import { useState, useRef } from 'react'
import './App.css'
import { Button, message, Tabs, Spin } from 'antd'
import type { TabsProps } from 'antd'
import axios from 'axios'

function App() {
  const urlInputRef = useRef<HTMLInputElement>(null)
  const fileInputRef = useRef<HTMLInputElement>(null)
  const [videoSrc, setVideoSrc] = useState<string>('')
  const [fileSrc, setFileSrc] = useState<string>('')
  const [segments, setSegments] = useState<string>('')
  const [loading, setLoading] = useState<boolean>(false)

  const handleFileUpload = () => {
    if (fileInputRef.current?.files && fileInputRef.current.files.length > 0) {
      const file = fileInputRef.current.files[0]
      const objectUrl = URL.createObjectURL(file)
      setFileSrc(objectUrl)
      message.success('File uploaded successfully')
    }
  }

  const previewVideo = () => {
    const url = urlInputRef.current?.value
    if (url && url.startsWith('http')) {
      setVideoSrc(url)
    } else if (fileInputRef.current?.files && fileInputRef.current.files.length > 0) {
      setVideoSrc(fileSrc)
    } else {
      message.error('Please either upload a video or enter URL first')
    }
  }

  const startProcessing = async () => {
    const url = urlInputRef.current?.value
    setLoading(true)
    try {
      if (url && url.startsWith('http')) {
        const res = await axios.post('http://localhost:8000/analyze/url', { url })
        setSegments(res.data.segments)
        message.success('Processed via URL')
      } else if (fileInputRef.current?.files && fileInputRef.current.files.length > 0) {
        const formData = new FormData()
        formData.append('file', fileInputRef.current.files[0])

        const res = await axios.post('http://localhost:8000/analyze/file', formData, {
          headers: { 'Content-Type': 'multipart/form-data' },
        })
        setSegments(res.data.segments)
        message.success('Processed via file')
      } else {
        message.error('Please either upload a video or enter URL first')
      }
    } catch (err) {
      console.error(err)
      message.error('Error processing the video')
    } finally {
      setLoading(false)
    }
  }

  const items: TabsProps['items'] = [
    {
      key: '1',
      label: 'Video Preview',
      children: videoSrc ? <video src={videoSrc} controls width="540" /> : <p>No video selected.</p>,
    },
    {
      key: '2',
      label: 'Analysis Result',
      children: segments ? (
        <pre style={{ whiteSpace: 'pre-wrap' }}>{segments}</pre>
      ) : (
        <p>No analysis result yet.</p>
      ),
    },
  ]

  return (
    <div className='container'>
      <div className="upload-container">
        <input
          type="file"
          accept="video/*"
          ref={fileInputRef}
          style={{ display: 'none' }}
          onChange={handleFileUpload}
        />
        <Button type='primary' onClick={() => fileInputRef.current?.click()}>Upload a video</Button>
        <span> or </span>
        <label>Enter url here: </label>
        <input className='custom-input' placeholder='URL' ref={urlInputRef} />
      </div>

      <Button style={{ marginRight: '10px' }} onClick={previewVideo}>Preview Video</Button>
      <Button onClick={startProcessing}>Start processing</Button>

      <div style={{ marginTop: '24px' }}>
        <Spin spinning={loading} tip="Processing video, please wait...">
          <Tabs defaultActiveKey="1" items={items} />
        </Spin>
      </div>
    </div>
  )
}

export default App
