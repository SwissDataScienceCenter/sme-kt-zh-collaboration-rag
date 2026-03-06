import React, { FunctionComponent } from "react";
import ReactMarkdown from "react-markdown";
import RemarkMath from "remark-math";
import RemarkBreaks from "remark-breaks";
import RehypeKatex from "rehype-katex";
import RemarkGfm from "remark-gfm";
import RehypeHighlight from "rehype-highlight";
import RehypeSanitize from "rehype-sanitize";
import RehypeRaw from "rehype-raw";
import { cn } from "@/lib/lorem";

export const Markdown: FunctionComponent<{ content: string }> = ({ content }) => (
    <ReactMarkdown
        remarkPlugins={[RemarkMath, RemarkGfm, RemarkBreaks]}
        rehypePlugins={[
            RehypeKatex,
            RehypeRaw,
            RehypeSanitize,
            [
                RehypeHighlight,
                {
                    detect: false,
                    ignoreMissing: true,
                },
            ],
        ]}
        components={{
            h1: ({ node, ...props }) => <h1 className="text-4xl font-bold mt-8 mb-4 text-foreground border-b pb-2" {...props} />,
            h2: ({ node, ...props }) => <h2 className="text-3xl font-bold mt-6 mb-3 text-foreground" {...props} />,
            h3: ({ node, ...props }) => <h3 className="text-2xl font-semibold mt-5 mb-2 text-foreground" {...props} />,
            h4: ({ node, ...props }) => <h4 className="text-xl font-semibold mt-4 mb-2 text-foreground" {...props} />,
            h5: ({ node, ...props }) => <h5 className="text-lg font-semibold mt-3 mb-1 text-foreground" {...props} />,
            h6: ({ node, ...props }) => <h6 className="text-base font-semibold mt-2 mb-1 text-muted-foreground" {...props} />,
            p: (pProps) => <p {...pProps} className={cn(pProps.className, "mb-4 leading-7 text-foreground")} dir="auto" />,
            a: (aProps) => {
                const href = aProps.href || "";
                const isInternal = /^\/#/i.test(href);
                const target = isInternal ? "_self" : aProps.target ?? "_blank";
                return (
                    <a
                        {...aProps}
                        href={href}
                        target={target}
                        rel="noopener noreferrer"
                        className={cn(
                            aProps.className,
                            "text-blue-600 dark:text-blue-400 hover:text-blue-700 dark:hover:text-blue-300 underline decoration-blue-600/30 hover:decoration-blue-600 transition-colors underline-offset-2",
                        )}
                    />
                );
            },
            code: (codeProps: any) => {
                const { inline, className: codeClass, children, ...props } = codeProps;
                if (inline) {
                    return (
                        <code {...props} className={cn(codeClass, "bg-muted text-foreground text-[0.875em] px-1.5 py-0.5 rounded font-mono")}>
                            {children}
                        </code>
                    );
                } else {
                    return (
                        <pre className={cn(codeClass, "bg-muted text-foreground text-sm p-4 rounded-lg overflow-x-auto my-4 border")}>
                            <code {...props} className={codeClass}>
                                {children}
                            </code>
                        </pre>
                    );
                }
            },
            pre: (preProps) => (
                <pre {...preProps} className={cn(preProps.className, "bg-muted text-foreground text-sm p-4 my-4 rounded-lg overflow-x-auto border")} />
            ),
            blockquote: (bqProps) => (
                <blockquote {...bqProps} className="border-l-4 border-muted-foreground/30 pl-4 py-1 italic my-4 text-muted-foreground bg-muted/30 rounded-r" />
            ),
            hr: () => <hr className="my-8 border-t border-border" />,
            ul: (ulProps) => <ul {...ulProps} className="list-disc list-outside ml-6 my-3 text-foreground space-y-1" />,
            ol: (olProps) => <ol {...olProps} className="list-decimal list-outside ml-6 my-3 text-foreground space-y-1" />,
            li: (liProps) => <li {...liProps} className="text-foreground leading-7 pl-1" />,
            input: ({ node, ...props }) => <input {...props} disabled className="mr-2 cursor-not-allowed accent-primary" />,
            strong: ({ node, ...props }) => <strong {...props} className="font-semibold text-foreground" />,
            em: ({ node, ...props }) => <em {...props} className="italic text-foreground" />,
            del: ({ node, ...props }) => <del {...props} className="line-through text-muted-foreground" />,
            table: (tableProps) => (
                <div className="my-6 overflow-x-auto">
                    <table {...tableProps} className="w-full border-collapse border border-border rounded-lg overflow-hidden text-sm" />
                </div>
            ),
            thead: (theadProps) => <thead {...theadProps} className="bg-muted" />,
            tbody: (tbodyProps) => <tbody {...tbodyProps} className="divide-y divide-border" />,
            tr: (trProps) => <tr {...trProps} className="border-b border-border last:border-0" />,
            th: (thProps) => <th {...thProps} className="px-4 py-3 font-semibold text-left text-foreground" />,
            td: (tdProps) => <td {...tdProps} className="px-4 py-3 text-left text-foreground" />,
        }}
    >
        {content}
    </ReactMarkdown>
);
