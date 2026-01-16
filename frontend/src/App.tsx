import { useState, useEffect } from 'react'
import './App.css'

interface TodoItem {
  id: number;
  title: string;
  completed: boolean;
}


const API_URL = "https://team1-backend-gucbckbgchbfa8bp.polandcentral-01.azurewebsites.net/";

function App() {
  const [todos, setTodos] = useState<TodoItem[]>([]);
  const [newTodo, setNewTodo] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    fetchTodos();
  }, []);

  const fetchTodos = async () => {
    try {
      const response = await fetch(`${API_URL}/todos`);
      if (!response.ok) throw new Error("Błąd pobierania danych");
      const data = await response.json();
      setTodos(data);
    } catch (err) {
      console.error(err);
      setError("Nie udało się połączyć z Backendem.");
    }
  };

  const handleAddTodo = async () => {
    if (!newTodo) return;
    setLoading(true);
    try {
      const response = await fetch(`${API_URL}/todos`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ title: newTodo })
      });

      if (response.ok) {
        setNewTodo("");
        fetchTodos();
      } else {
        alert("Błąd podczas dodawania!");
      }
    } catch (err) {
      alert("Błąd sieci!");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="card">
      <h1>☁️ Azure Team 1 To-Do App</h1>

      {/* Sekcja dodawania */}
      <div style={{ marginBottom: '20px' }}>
        <input
          type="text"
          value={newTodo}
          onChange={(e) => setNewTodo(e.target.value)}
          placeholder="Co trzeba zrobić?"
          style={{ padding: '10px', marginRight: '10px' }}
        />
        <button onClick={handleAddTodo} disabled={loading}>
          {loading ? "Wysyłanie..." : "Dodaj"}
        </button>
      </div>

      {/* Lista zadań */}
      {error && <p style={{ color: 'red' }}>{error}</p>}

      <ul style={{ listStyle: 'none', padding: 0 }}>
        {todos.map((todo) => (
          <li key={todo.id} style={{
            background: '#2a2a2a',
            margin: '10px 0',
            padding: '10px',
            borderRadius: '5px',
            textAlign: 'left'
          }}>
            {todo.completed ? "✅" : "⬜"} <strong>{todo.title}</strong>
          </li>
        ))}
      </ul>
    </div>
  )
}

export default App