"use client"

import { useState } from "react"
import s from "./MyFriends.module.css"

export default function MyFriends() {
  const [theme, setTheme] = useState("colorful")
  const [friends, setFriends] = useState([
    {
      id: 1,
      username: "sarah_johnson",
      fullName: "Sarah Johnson",
      avatar: "/diverse-woman-avatar.png",
      isFollowing: true,
      mutualFriends: 12,
    },
    {
      id: 2,
      username: "mike_chen",
      fullName: "Mike Chen",
      avatar: "/man-avatar.png",
      isFollowing: true,
      mutualFriends: 8,
    },
    {
      id: 3,
      username: "emma_davis",
      fullName: "Emma Davis",
      avatar: "/woman-glasses-avatar.jpg",
      isFollowing: true,
      mutualFriends: 15,
    },
    {
      id: 4,
      username: "alex_rodriguez",
      fullName: "Alex Rodriguez",
      avatar: "/man-beard-avatar.png",
      isFollowing: true,
      mutualFriends: 6,
    },
    {
      id: 5,
      username: "lisa_kim",
      fullName: "Lisa Kim",
      avatar: "/diverse-person-avatars.png",
      isFollowing: true,
      mutualFriends: 20,
    },
  ])

  const handleFollowToggle = (friendId) => {
    setFriends(
      friends.map((friend) => (friend.id === friendId ? { ...friend, isFollowing: !friend.isFollowing } : friend)),
    )
  }

  const handleNavigation = (page) => {
    console.log(`Navigating to ${page}`)
  }

  return (
    <div className={`${s.container} ${s[theme]}`}>
      {/* Header */}
      <header className={s.header}>
        <div className={s.headerContent}>
          <h1 className={s.title}>My Friends</h1>
          <button
            onClick={() => setTheme(theme === "colorful" ? "formal" : "colorful")}
            className={s.themeToggle}
            aria-label="Toggle theme"
          >
            {theme === "colorful" ? "🎨" : "💼"}
          </button>
        </div>
        <p className={s.subtitle}>{friends.filter((f) => f.isFollowing).length} friends</p>
      </header>

      {/* Friends List */}
      <main className={s.main}>
        <div className={s.friendsList}>
          {friends.map((friend) => (
            <div key={friend.id} className={s.friendCard}>
              <div className={s.friendInfo}>
                <img
                  src={friend.avatar || "/placeholder.svg"}
                  alt={`${friend.fullName}'s avatar`}
                  className={s.avatar}
                />
                <div className={s.userDetails}>
                  <h3 className={s.username}>{friend.username}</h3>
                  <p className={s.fullName}>{friend.fullName}</p>
                  <p className={s.mutualFriends}>{friend.mutualFriends} mutual friends</p>
                </div>
              </div>
              <button
                onClick={() => handleFollowToggle(friend.id)}
                className={`${s.followButton} ${friend.isFollowing ? s.following : s.notFollowing}`}
                aria-label={friend.isFollowing ? `Unfollow ${friend.username}` : `Follow ${friend.username}`}
              >
                {friend.isFollowing ? "Following" : "Follow"}
              </button>
            </div>
          ))}
        </div>
      </main>

      {/* Bottom Navigation */}
      <nav className={s.bottomNav} role="navigation" aria-label="Main navigation">
        <button onClick={() => handleNavigation("findbook")} className={s.navButton} aria-label="Find Book">
          <svg className={s.navIcon} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20" />
            <path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z" />
          </svg>
          <span className={s.navLabel}>Find Book</span>
        </button>

        <button onClick={() => handleNavigation("findfriends")} className={s.navButton} aria-label="Find Friends">
          <svg className={s.navIcon} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <circle cx="12" cy="8" r="5" />
            <path d="M20 21a8 8 0 1 0-16 0" />
            <path d="M12 13v8" />
            <path d="M8 17h8" />
          </svg>
          <span className={s.navLabel}>Find Friends</span>
        </button>

        <button onClick={() => handleNavigation("searchprompts")} className={s.navButton} aria-label="Search Prompts">
          <svg className={s.navIcon} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <circle cx="11" cy="11" r="8" />
            <path d="m21 21-4.35-4.35" />
          </svg>
          <span className={s.navLabel}>Search</span>
        </button>

        <button
          onClick={() => handleNavigation("friends")}
          className={`${s.navButton} ${s.active}`}
          aria-label="Friends"
          aria-current="page"
        >
          <svg className={s.navIcon} viewBox="0 0 24 24" fill="currentColor" stroke="currentColor" strokeWidth="2">
            <path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2" />
            <circle cx="9" cy="7" r="4" />
            <path d="M22 21v-2a4 4 0 0 0-3-3.87" />
            <path d="M16 3.13a4 4 0 0 1 0 7.75" />
          </svg>
          <span className={s.navLabel}>Friends</span>
        </button>

        <button onClick={() => handleNavigation("feed")} className={s.navButton} aria-label="Feed">
          <svg className={s.navIcon} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <rect x="3" y="3" width="18" height="18" rx="2" />
            <path d="M3 9h18" />
            <path d="M9 21V9" />
          </svg>
          <span className={s.navLabel}>Feed</span>
        </button>

        <button onClick={() => handleNavigation("me")} className={s.navButton} aria-label="Profile">
          <svg className={s.navIcon} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M19 21v-2a4 4 0 0 0-4-4H9a4 4 0 0 0-4 4v2" />
            <circle cx="12" cy="7" r="4" />
          </svg>
          <span className={s.navLabel}>Me</span>
        </button>
      </nav>
    </div>
  )
}
