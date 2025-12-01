"use client";

import { useState } from 'react'
import { supabase } from '../lib/supabase'

export default function Auth({ onLogin }) {
    const [loading, setLoading] = useState(false)
    const [email, setEmail] = useState('')
    const [message, setMessage] = useState('')

    const handleLogin = async (event) => {
        event.preventDefault()

        setLoading(true)
        const { error } = await supabase.auth.signInWithOtp({ email })

        if (error) {
            setMessage(error.error_description || error.message)
        } else {
            setMessage('Check your email for the login link!')
        }
        setLoading(false)
    }

    return (
        <div className="flex flex-col items-center justify-center p-8 bg-white/[0.02] rounded-3xl border border-white/5 backdrop-blur-sm">
            <h1 className="text-2xl font-medium text-white mb-2">Welcome Back</h1>
            <p className="text-slate-400 text-sm mb-6 text-center">
                Sign in via magic link to access your dashboard
            </p>
            {message && (
                <div className="bg-violet-500/10 text-violet-200 border border-violet-500/20 p-3 rounded-xl mb-6 text-sm w-full text-center">
                    {message}
                </div>
            )}
            <form onSubmit={handleLogin} className="w-full space-y-4">
                <div>
                    <input
                        className="w-full bg-black/20 border border-white/10 rounded-xl px-4 py-3 text-white placeholder:text-slate-500 focus:border-violet-500 focus:outline-none transition-colors"
                        type="email"
                        placeholder="name@example.com"
                        value={email}
                        required={true}
                        onChange={(e) => setEmail(e.target.value)}
                    />
                </div>
                <div>
                    <button
                        className="w-full bg-white text-black hover:bg-slate-200 font-medium py-3 rounded-xl transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                        disabled={loading}
                    >
                        {loading ? <span>Sending...</span> : <span>Send Magic Link</span>}
                    </button>
                </div>
            </form>
        </div>
    )
}
