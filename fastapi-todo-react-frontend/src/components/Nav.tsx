import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";


export default function Nav() {

    const [isMenuOpen, setIsMenuOpen] = useState(false)
    const { isAuthenticated, user, logout } = useAuth()
    const navigate = useNavigate()

    const handleLogout = () => {
        logout()
        setIsMenuOpen(false)
        navigate('/login')
    }

    const toggleMenu = () => setIsMenuOpen(!isMenuOpen);
    const closeMenu = () => setIsMenuOpen(false);

    return (
        <header className={`site-nav ${isMenuOpen ? 'site-nav--open' : ''}`}>
            <div className="site-nav__container">
                <Link to="/" className="site-nav__logo" onClick={closeMenu}>
                    <span className="site-nav__logo-icon">✓</span>
                    <span className="site-nav__logo-text">TaskFlow</span>
                </Link>

                <nav className="site-nav__menu">
                    <Link to="/" className="site-nav__link" onClick={closeMenu}>Home</Link>
                    {isAuthenticated ? (
                        <>
                            <Link to="/todos" className="site-nav__link" onClick={closeMenu}>Todo's</Link>
                            <Link to="/add" className="site-nav__link site-nav__link--cta" onClick={closeMenu}>Add Todo</Link>
                            <span className="site-nav__user" data-testid="nav-user">{user?.email}</span>
                            <button type="button" className="site-nav__logout" onClick={handleLogout}>Log out</button>
                        </>
                    ) : (
                        <Link to="/login" className="site-nav__link site-nav__link--cta" onClick={closeMenu}>Sign in</Link>
                    )}
                </nav>

                <button className="site-nav__hamburger" onClick={toggleMenu} aria-label="Toggle menu">
                    <span className="site-nav__hamburger-bar"></span>
                    <span className="site-nav__hamburger-bar"></span>
                    <span className="site-nav__hamburger-bar"></span>
                </button>
            </div>
            {isMenuOpen && <div className="site-nav__overlay" onClick={closeMenu}></div>}
        </header>
    )

}