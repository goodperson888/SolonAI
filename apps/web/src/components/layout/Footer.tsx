export const Footer = () => {
  return (
    <footer className="mt-auto border-t border-gray-800 bg-gray-950">
      <div className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
        <div className="grid grid-cols-1 gap-8 md:grid-cols-4">
          {/* Brand */}
          <div className="col-span-1">
            <div className="mb-4 flex items-center space-x-2">
              <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-gradient-to-r from-indigo-600 to-purple-600">
                <span className="text-xl font-bold text-white">S</span>
              </div>
              <span className="text-xl font-bold text-white">Solon AI</span>
            </div>
            <p className="text-sm text-gray-400">Solana生态全链路非托管AI金融智能体</p>
          </div>

          {/* Links */}
          <div>
            <h3 className="mb-4 text-sm font-semibold text-white">产品</h3>
            <ul className="space-y-2">
              <li>
                <a href="#" className="text-sm text-gray-400 transition-colors hover:text-white">
                  功能特性
                </a>
              </li>
              <li>
                <a href="#" className="text-sm text-gray-400 transition-colors hover:text-white">
                  定价
                </a>
              </li>
              <li>
                <a href="#" className="text-sm text-gray-400 transition-colors hover:text-white">
                  文档
                </a>
              </li>
            </ul>
          </div>

          <div>
            <h3 className="mb-4 text-sm font-semibold text-white">资源</h3>
            <ul className="space-y-2">
              <li>
                <a href="#" className="text-sm text-gray-400 transition-colors hover:text-white">
                  博客
                </a>
              </li>
              <li>
                <a href="#" className="text-sm text-gray-400 transition-colors hover:text-white">
                  教程
                </a>
              </li>
              <li>
                <a href="#" className="text-sm text-gray-400 transition-colors hover:text-white">
                  社区
                </a>
              </li>
            </ul>
          </div>

          <div>
            <h3 className="mb-4 text-sm font-semibold text-white">关于</h3>
            <ul className="space-y-2">
              <li>
                <a href="#" className="text-sm text-gray-400 transition-colors hover:text-white">
                  关于我们
                </a>
              </li>
              <li>
                <a href="#" className="text-sm text-gray-400 transition-colors hover:text-white">
                  联系我们
                </a>
              </li>
              <li>
                <a href="#" className="text-sm text-gray-400 transition-colors hover:text-white">
                  隐私政策
                </a>
              </li>
            </ul>
          </div>
        </div>

        <div className="mt-8 border-t border-gray-800 pt-8">
          <p className="text-center text-sm text-gray-400">© 2026 Solon AI. All rights reserved.</p>
        </div>
      </div>
    </footer>
  )
}
