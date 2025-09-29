"use client"

import { useState } from "react"
import s from "./Feed.module.css"

export default function Feed() {
  const [theme, setTheme] = useState("colorful")
  const [feedPosts, setFeedPosts] = useState([
    {
      id: 1,
      user: {
        username: "bookworm_sarah",
        avatar: "/diverse-woman-avatar.png",
        isFollowing: false,
      },
      prompt:
        "Looking for mystery novels with strong female protagonists set in Victorian England. Any recommendations?",
      likes: 234,
      isLiked: false,
      timestamp: "2h ago",
    },
    {
      id: 2,
      user: {
        username: "literary_mike",
        avatar: "/man-avatar.png",
        isFollowing: true,
      },
      prompt:
        'Can anyone suggest sci-fi books that explore AI consciousness and ethics? Similar to "Do Androids Dream of Electric Sheep?"',
      likes: 567,
      isLiked: true,
      timestamp: "4h ago",
    },
    {
      id: 3,
      user: {
        username: "fantasy_reader",
        avatar: "/diverse-person-avatars.png",
        isFollowing: false,
      },
      prompt:
        "Need epic fantasy series recommendations with complex magic systems and political intrigue. Already read Brandon Sanderson!",
      likes: 892,
      isLiked: false,
      timestamp: "6h ago",
    },
    {
      id: 4,
      user: {
        username: "history_buff",
        avatar: "/woman-glasses-avatar.jpg",
        isFollowing: true,
      },
      prompt:
        "Searching for historical fiction about ancient Rome. Prefer books that balance accuracy with engaging storytelling.",
      likes: 445,
      isLiked: true,
      timestamp: "8h ago",
    },
    {
      id: 5,
      user: {
        username: "thriller_fan",
        avatar: "/man-beard-avatar.png",
        isFollowing: false,
      },
      prompt:
        "What are the best psychological thrillers of 2024? Looking for books that keep you guessing until the very end.",
      likes: 678,
      isLiked: false,
      timestamp: "10h ago",
    },
  ])

  const handleFollowToggle = (postId) => {
    setFeedPosts(
      feedPosts.map((post) =>
        post.id === postId ? { ...post, user: { ...post.user, isFollowing: !post.user.isFollowing } } : post,
      ),
    )
  }

  const handleLikeToggle = (postId) => {
    setFeedPosts(
      feedPosts.map((post) =>
        post.id === postId
          ? {
              ...post,
              isLiked: !post.isLiked,
              likes: post.isLiked ? post.likes - 1 : post.likes + 1,
            }
          : post,
      ),
    )
  }

  const handleNavigation = (page) => {
    console.log(`Navigate to: ${page}`)
  }

  return (
    <div className={`${s.container} ${s[theme]}`}>
      <header className={s.header}>
        <h1 className={s.title}>Feed</h1>
        <div className={s.themeToggle}>
          <button
            onClick={() => setTheme("colorful")}
            className={`${s.themeBtn} ${theme === "colorful" ? s.active : ""}`}
            aria-label="Switch to colorful theme"
          >
            Colorful
          </button>
          <button
            onClick={() => setTheme("formal")}
            className={`${s.themeBtn} ${theme === "formal" ? s.active : ""}`}
            aria-label="Switch to formal theme"
          >
            Formal
          </button>
        </div>
      </header>

      <main className={s.main}>
        <div className={s.feedContainer}>
          {feedPosts.map((post) => (
            <article key={post.id} className={s.postCard}>
              <div className={s.postHeader}>
                <div className={s.userInfo}>
                  <img
                    src={post.user.avatar || "/placeholder.svg"}
                    alt={`${post.user.username}'s avatar`}
                    className={s.avatar}
                  />
                  <span className={s.username}>{post.user.username}</span>
                  <span className={s.timestamp}>{post.timestamp}</span>
                </div>
                <button
                  onClick={() => handleFollowToggle(post.id)}
                  className={`${s.followBtn} ${post.user.isFollowing ? s.following : ""}`}
                  aria-label={post.user.isFollowing ? `Unfollow ${post.user.username}` : `Follow ${post.user.username}`}
                >
                  {post.user.isFollowing ? "Following" : "Follow"}
                </button>
              </div>

              <div className={s.postContent}>
                <p className={s.promptText}>{post.prompt}</p>
              </div>

              <div className={s.postFooter}>
                <button
                  onClick={() => handleLikeToggle(post.id)}
                  className={`${s.likeBtn} ${post.isLiked ? s.liked : ""}`}
                  aria-label={post.isLiked ? "Unlike post" : "Like post"}
                >
                  <svg
                    className={s.heartIcon}
                    viewBox="0 0 24 24"
                    fill={post.isLiked ? "currentColor" : "none"}
                    stroke="currentColor"
                    strokeWidth="2"
                  >
                    <path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z" />
                  </svg>
                  <span className={s.likeCount}>{post.likes.toLocaleString()}</span>
                </button>
              </div>
            </article>
          ))}
        </div>
      </main>

      <nav className={s.bottomNav} role="navigation" aria-label="Main navigation">
        <button onClick={() => handleNavigation("findbook")} className={s.navBtn} aria-label="Find Book">
          <svg className={s.navIcon} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20" />
            <path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z" />
          </svg>
          <span className={s.navLabel}>Find Book</span>
        </button>
        <button onClick={() => handleNavigation("friends")} className={s.navBtn} aria-label="Friends">
          <svg className={s.navIcon} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2" />
            <circle cx="9" cy="7" r="4" />
            <path d="M23 21v-2a4 4 0 0 0-3-3.87" />
            <path d="M16 3.13a4 4 0 0 1 0 7.75" />
          </svg>
          <span className={s.navLabel}>Friends</span>
        </button>
        <button onClick={() => handleNavigation("prompts")} className={s.navBtn} aria-label="Prompts">
          <svg className={s.navIcon} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
          </svg>
          <span className={s.navLabel}>Prompts</span>
        </button>
        <button
          onClick={() => handleNavigation("feed")}
          className={`${s.navBtn} ${s.active}`}
          aria-label="Feed"
          aria-current="page"
        >
          <svg className={s.navIcon} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <rect x="3" y="3" width="7" height="7" />
            <rect x="14" y="3" width="7" height="7" />
            <rect x="14" y="14" width="7" height="7" />
            <rect x="3" y="14" width="7" height="7" />
          </svg>
          <span className={s.navLabel}>Feed</span>
        </button>
        <button onClick={() => handleNavigation("me")} className={s.navBtn} aria-label="Profile">
          <svg className={s.navIcon} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2" />
            <circle cx="12" cy="7" r="4" />
          </svg>
          <span className={s.navLabel}>Me</span>
        </button>
      </nav>
    </div>
  )
}
