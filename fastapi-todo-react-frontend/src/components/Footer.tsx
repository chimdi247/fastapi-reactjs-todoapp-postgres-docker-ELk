import { Link } from "react-router-dom"

export default function Footer() {

    const currentYear = new Date().getFullYear()

    return (
        <footer className="site-footer">
            <div className="site-footer__container">
                <div className="site-footer__grid">
                    {/* Brand Column */}
                    <div className="site-footer__col site-footer__col--brand">
                        <h3 className="site-footer__brand-name">TaskFlow</h3>
                        <p className="site-footer__brand-desc">
                            A beautifully simple way to organize your day, track your progress, and achieve your goals.
                        </p>
                    </div>

                    {/* Navigation Column */}
                    <div className="site-footer__col">
                        <h4 className="site-footer__col-title">Navigation</h4>
                        <ul className="site-footer__list">
                            <li><Link to="/" className="site-footer__link">Home</Link></li>
                            <li><Link to="/todos" className="site-footer__link">My Todo's</Link></li>
                            <li><Link to="/add" className="site-footer__link">Add New Todo</Link></li>
                        </ul>
                    </div>

                    {/* Resources Column */}
                    <div className="site-footer__col">
                        <h4 className="site-footer__col-title">Resources</h4>
                        <ul className="site-footer__list">
                            <li><a href="#" className="site-footer__link">Documentation</a></li>
                            <li><a href="#" className="site-footer__link">Support</a></li>
                            <li><a href="#" className="site-footer__link">Privacy Policy</a></li>
                        </ul>
                    </div>
                </div>

                {/* Bottom Bar */}
                <div className="site-footer__bottom">
                    <p className="site-footer__copyright">
                        &copy; {currentYear} TaskFlow. Crafted with care.
                    </p>
                    <div className="site-footer__socials">
                        <a href="#" className="site-footer__social-link" aria-label="Twitter">𝕏</a>
                        <a href="#" className="site-footer__social-link" aria-label="GitHub">⌘</a>
                        <a href="#" className="site-footer__social-link" aria-label="LinkedIn">in</a>
                    </div>
                </div>
            </div>
        </footer>
    )

}