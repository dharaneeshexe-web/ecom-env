"use client";

import { motion } from "framer-motion";
import { LucideIcon } from "lucide-react";

const AIActionCard = () => {
  return (
    <motion.div
      initial={{ opacity: 0, y: 50 }}
      animate={{ opacity: 1, y: 0 }}
      whileHover={{ scale: 1.03, boxShadow: "0 0 20px rgba(99, 102, 241, 0.8)" }}
      transition={{ duration: 0.5 }}
      className="bg-opacity-50 bg-black rounded-2xl p-6 shadow-glow border border-purple-500"
    >
      <h2 className="text-2xl font-bold text-purple-400">AI Decision Card</h2>
      <p className="text-lg">Product Price: ₹350</p>
      <p className="text-lg">Rating: ⭐⭐⭐⭐</p>
      <p className="text-lg">Fraud Risk: 🚨</p>
      <p className="text-lg">Return Reason: Damaged</p>
      <p className="text-lg">Days Since Purchase: 5</p>
    </motion.div>
  );
};

export default AIActionCard;