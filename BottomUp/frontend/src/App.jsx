import React, {useState, useEffect, useRef} from 'react'

export default function App(){
  const [spec, setSpec] = useState('')
  const [status, setStatus] = useState('idle')
  const [logs, setLogs] = useState([])
  const wsRef = useRef(null)
  const [zipUrl, setZipUrl] = useState(null)

  useEffect(() => {
    wsRef.current = new WebSocket('ws://localhost:8000/ws/logs')
    wsRef.current.onmessage = (e) => {
      setLogs(l => [...l, e.data])
    }
    return () => wsRef.current.close()
  }, [])

  const run = async () => {
    setStatus('running')
    setLogs([])
    const res = await fetch('http://localhost:8000/api/run', {
      method: 'POST',
      headers: {'Content-Type':'application/json'},
      body: JSON.stringify({spec})
    })
    const json = await res.json()
    if(json.zip){
      setZipUrl(json.zip)
    }
    setStatus('done')
  }

  return (<div style={{fontFamily:'system-ui, Arial', padding:20}}>
    <h1>Bottom-up Groq Agents — UI</h1>
    <p>Enter a project spec and run the pipeline.</p>
    <textarea value={spec} onChange={e=>setSpec(e.target.value)} rows={6} cols={80} />
    <div style={{marginTop:10}}>
      <button onClick={run} disabled={status==='running'}>Run</button>
    </div>
    <h3>Logs</h3>
    <div style={{whiteSpace:'pre-wrap', background:'#f5f5f5', padding:10, minHeight:200}}>
      {logs.map((l,i)=> <div key={i}>[{i+1}] {l}</div>)}
    </div>
    {zipUrl && (<div style={{marginTop:10}}>
      <a href={zipUrl} target='_blank' rel='noreferrer'>Download generated project</a>
    </div>)}
  </div>)
}
