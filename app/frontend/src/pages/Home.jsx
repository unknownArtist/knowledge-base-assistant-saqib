// Home.jsx
import { useState } from "react";
import logo from "../assets/Logo.png";
import bgImage from "../assets/bg-image.png";
import SearchBar from "../components/SearchBar";
import ArticleCard from "../components/ArticleCard";
import ChatBox from "../components/ChatBox";

function Home() {
  const [selectedArticle, setSelectedArticle] = useState(null);
  const [loadingArticle, setLoadingArticle] = useState(false);
  const [showChat, setShowChat] = useState(false);

  // On typing the previous cards will disappear
  function handleSearchTyping() {
    setSelectedArticle(null);
    setShowChat(false);
  }

  function handleSelectArticle(id, item) {
    setLoadingArticle(true);
    setShowChat(false);

    // pretend to fetch article (replace with real API later)
    setTimeout(() => {
      setSelectedArticle({
        id: item.id,
        title: item.title,
        content: item.content,
        author_name: item.author_name,
        published_date: item.published_date,
        category_name: item.category_name,
        tags: item.tags ? item.tags.map((tag) => tag.name) : [],
      });
      setLoadingArticle(false);
    }, 1000);
  }

  return (
    <div
      className="min-h-screen w-full bg-cover bg-center bg-no-repeat bg-fixed relative"
      style={{ backgroundImage: `url(${bgImage})` }}
    >
      {/* Main wrapper */}
      <div className="min-h-screen flex flex-col items-center p-6">
        {/* Header */}
        <header className="flex flex-col items-center mt-10 mb-12">
          <img src={logo} alt="App Logo" className="w-32 h-32 mb-4" />
          <h1 className="text-4xl font-extrabold text-white text-center drop-shadow">
            Knowledge Base Assistant
          </h1>
          <p className="mt-2 text-gray-200 text-lg text-center">
            Search articles, explore insights, and ask AI for answers.
          </p>
        </header>

        {/* SearchBar centered */}
        <main className="w-full max-w-4xl flex flex-col items-center">
          <div className="w-full max-w-2xl">
            <SearchBar
              onSelectArticle={handleSelectArticle}
              onTyping={handleSearchTyping}
            />
          </div>

          {/* Loading Spinner */}
          {loadingArticle && (
            <div className="flex justify-center items-center mt-6 h-40">
              <div className="w-10 h-10 border-4 border-gray-300 border-t-blue-500 rounded-full animate-spin"></div>
            </div>
          )}

          {/* Show article card and chat */}
          {selectedArticle && (
            <div className="w-full mt-6 flex flex-col items-center">
              <ArticleCard
                article={selectedArticle}
                onAsk={() => setShowChat(true)}
                onClose={() => {
                  setSelectedArticle(null);
                  setShowChat(false);
                }}
              />
              {showChat && (
                <div className="w-full max-w-2xl mt-6">
                  <ChatBox articleId={selectedArticle.id} />
                </div>
              )}
            </div>
          )}
        </main>
      </div>
    </div>
  );
}

export default Home;
