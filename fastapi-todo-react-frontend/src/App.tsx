
import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom'
import './App.css'
import Nav from './components/Nav'
import Footer from './components/Footer'
import Home from './pages/Home'
import AllTodos from './pages/AllTodos'
import AddTodo from './pages/AddTodo'
import EditTodo from './pages/EditTodo'
import Login from './pages/Login'
import ProtectedRoute from './components/ProtectedRoute'
import { AuthProvider } from './context/AuthContext'



function App() {

  return (
    <BrowserRouter>
      <AuthProvider>
      <Nav />

      <main>

        <Routes>

          <Route path='/' element={<Home />} />
          <Route path='/home' element={<Home />} />
          <Route path='/login' element={<Login />} />

          <Route element={<ProtectedRoute />}>
            <Route path='/todos' element={<AllTodos />} />
            <Route path='/add' element={<AddTodo />} />
            <Route path='/todos/:id/edit' element={<EditTodo />} />
          </Route>

          <Route path='*' element={<Navigate to={"/"} replace />} />

        </Routes>

      </main>

      <Footer />
      </AuthProvider>
    </BrowserRouter>
  )
}

export default App
